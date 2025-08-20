import asyncio
import time
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import IngestLogger, get_logger
from app.core.timeutil import get_current_date, get_effective_date
from app.data.fmp_adapter import get_fmp_adapter
from app.data.mapping import (
    get_indicators_by_source_api,
    extract_indicator_value,
    get_indicator_mapping
)
from app.data.repositories import CoreIndicatorsRepository
from app.db.models import IndicatorCatalog
from app.schemas.ingest import IngestResult

logger = get_logger(__name__)


class IngestService:
    """Service for ingesting core indicators data."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fmp_adapter = get_fmp_adapter()
        self.repository = CoreIndicatorsRepository(session)
    
    async def ingest_symbol(
        self, 
        symbol: str, 
        target_date: Optional[date] = None
    ) -> IngestResult:
        """Ingest core indicators for a single symbol."""
        
        if target_date is None:
            target_date = get_current_date()
        
        ingest_logger = IngestLogger(symbol, str(target_date))
        start_time = time.time()
        
        try:
            ingest_logger.log_start()
            
            # Get core indicators from catalog
            core_indicators = await self._get_core_indicators()
            if not core_indicators:
                error_msg = "No core indicators found in catalog"
                ingest_logger.log_error(error_msg)
                return IngestResult(
                    symbol=symbol,
                    date=target_date,
                    total_indicators=0,
                    non_null_indicators=0,
                    coverage=0.0,
                    duration_ms=0,
                    success=False,
                    error=error_msg
                )
            
            # Group indicators by source API
            api_groups = self._group_indicators_by_api(core_indicators)
            
            # Collect all indicator values
            all_indicators_data = []
            
            for source_api, indicators in api_groups.items():
                try:
                    # Fetch data from API
                    api_data = await self.fmp_adapter.fetch_by_source_api(source_api, symbol)
                    
                    if api_data is None:
                        # API call failed, mark all indicators as failed
                        for indicator in indicators:
                            all_indicators_data.append({
                                "indicator_id": indicator.indicator_id,
                                "value": None,
                                "currency": None,
                                "source": source_api,
                                "null_reason": "API_ERROR"
                            })
                        ingest_logger.log_api_error(source_api, "API call failed")
                        continue
                    
                    # Extract values for each indicator
                    for indicator in indicators:
                        value = extract_indicator_value(api_data, indicator.indicator_id)
                        
                        all_indicators_data.append({
                            "indicator_id": indicator.indicator_id,
                            "value": value,
                            "currency": self._get_currency_for_indicator(indicator),
                            "source": source_api,
                            "null_reason": None if value is not None else "NO_DATA"
                        })
                
                except Exception as e:
                    # API group failed, mark all indicators as failed
                    for indicator in indicators:
                        all_indicators_data.append({
                            "indicator_id": indicator.indicator_id,
                            "value": None,
                            "currency": None,
                            "source": source_api,
                            "null_reason": "API_ERROR"
                        })
                    ingest_logger.log_api_error(source_api, str(e))
            
            # Store in database
            await self.repository.bulk_upsert_indicators(
                stock_id=symbol,
                date=target_date,
                indicators_data=all_indicators_data
            )
            
            # Calculate coverage
            total_indicators = len(all_indicators_data)
            non_null_indicators = sum(
                1 for data in all_indicators_data 
                if data["value"] is not None
            )
            coverage = non_null_indicators / total_indicators if total_indicators > 0 else 0.0
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            ingest_logger.log_completion(
                total_indicators, non_null_indicators, coverage, duration_ms
            )
            
            return IngestResult(
                symbol=symbol,
                date=target_date,
                total_indicators=total_indicators,
                non_null_indicators=non_null_indicators,
                coverage=coverage,
                duration_ms=duration_ms,
                success=True
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Unexpected error: {str(e)}"
            ingest_logger.log_error(error_msg)
            
            return IngestResult(
                symbol=symbol,
                date=target_date,
                total_indicators=0,
                non_null_indicators=0,
                coverage=0.0,
                duration_ms=duration_ms,
                success=False,
                error=error_msg
            )
    
    async def ingest_multiple_symbols(
        self, 
        symbols: List[str], 
        target_date: Optional[date] = None
    ) -> List[IngestResult]:
        """Ingest core indicators for multiple symbols."""
        results = []
        
        # Process symbols concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def ingest_with_semaphore(symbol: str) -> IngestResult:
            async with semaphore:
                return await self.ingest_symbol(symbol, target_date)
        
        # Create tasks for all symbols
        tasks = [ingest_with_semaphore(symbol) for symbol in symbols]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result for failed ingestions
                error_result = IngestResult(
                    symbol=symbols[i],
                    date=target_date or get_current_date(),
                    total_indicators=0,
                    non_null_indicators=0,
                    coverage=0.0,
                    duration_ms=0,
                    success=False,
                    error=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _get_core_indicators(self) -> List[IndicatorCatalog]:
        """Get all active core indicators from catalog."""
        from app.data.repositories import IndicatorCatalogRepository
        
        catalog_repo = IndicatorCatalogRepository(self.session)
        return await catalog_repo.get_all_core_indicators()
    
    def _group_indicators_by_api(
        self, 
        indicators: List[IndicatorCatalog]
    ) -> Dict[str, List[IndicatorCatalog]]:
        """Group indicators by their source API."""
        groups = {}
        
        for indicator in indicators:
            source_api = indicator.source_api
            if source_api not in groups:
                groups[source_api] = []
            groups[source_api].append(indicator)
        
        return groups
    
    def _get_currency_for_indicator(self, indicator: IndicatorCatalog) -> Optional[str]:
        """Get currency for an indicator based on its unit."""
        if indicator.unit == "USD":
            return "USD"
        return None
