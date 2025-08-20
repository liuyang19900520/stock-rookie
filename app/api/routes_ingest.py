import time
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.data.ingest_service import IngestService
from app.data.repositories import CoreIndicatorsRepository
from app.schemas.ingest import (
    IngestRequest,
    IngestResponse,
    CoreIndicatorsLatest,
    CoreIndicatorValue
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["ingest"])


@router.post("/ingest/core", response_model=IngestResponse)
async def ingest_core_indicators(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db)
) -> IngestResponse:
    """Ingest core indicators for specified symbols."""
    start_time = time.time()
    
    try:
        # Validate request
        if not request.symbols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one symbol must be provided"
            )
        
        if len(request.symbols) > 100:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 symbols allowed per request"
            )
        
        # Perform ingestion sequentially to avoid database session conflicts
        results = []
        for symbol in request.symbols:
            try:
                # Create a new service instance for each symbol
                service = IngestService(db)
                result = await service.ingest_symbol(symbol, request.date)
                results.append(result)
            except Exception as e:
                logger.error(f"Error ingesting {symbol}: {e}")
                # Create error result
                from app.schemas.ingest import IngestResult
                from app.core.timeutil import get_current_date
                error_result = IngestResult(
                    symbol=symbol,
                    date=request.date or get_current_date(),
                    total_indicators=0,
                    non_null_indicators=0,
                    coverage=0.0,
                    duration_ms=0,
                    success=False,
                    error=str(e)
                )
                results.append(error_result)
        
        # Calculate overall statistics
        total_symbols = len(results)
        successful_symbols = sum(1 for r in results if r.success)
        failed_symbols = total_symbols - successful_symbols
        overall_duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Ingest completed: {total_symbols} symbols, "
            f"{successful_symbols} successful, {failed_symbols} failed, "
            f"duration={overall_duration_ms}ms"
        )
        
        return IngestResponse(
            results=results,
            total_symbols=total_symbols,
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols,
            overall_duration_ms=overall_duration_ms,
            timestamp=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during ingest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest core indicators"
        )


@router.get("/tickers/{symbol}/core/latest", response_model=CoreIndicatorsLatest)
async def get_latest_core_indicators(
    symbol: str,
    db: AsyncSession = Depends(get_db)
) -> CoreIndicatorsLatest:
    """Get latest core indicators for a ticker."""
    try:
        repo = CoreIndicatorsRepository(db)
        
        # Get latest indicators
        indicators_dict = await repo.get_latest_indicators(symbol)
        
        if not indicators_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No indicators found for symbol {symbol}"
            )
        
        # Convert to response format
        indicators = {}
        total_indicators = len(indicators_dict)
        non_null_indicators = 0
        latest_date = None
        latest_as_of_time = None
        
        for indicator_id, record in indicators_dict.items():
            if record.value is not None:
                non_null_indicators += 1
            
            if latest_date is None or record.date > latest_date:
                latest_date = record.date
            
            if latest_as_of_time is None or record.as_of_time > latest_as_of_time:
                latest_as_of_time = record.as_of_time
            
            indicators[indicator_id] = CoreIndicatorValue(
                indicator_id=record.indicator_id,
                value=record.value,
                unit="",  # Would need to get from catalog
                currency=record.currency,
                date=record.date,
                source=record.source,
                null_reason=record.null_reason
            )
        
        coverage = non_null_indicators / total_indicators if total_indicators > 0 else 0.0
        
        return CoreIndicatorsLatest(
            symbol=symbol,
            date=latest_date,
            indicators=indicators,
            total_indicators=total_indicators,
            non_null_indicators=non_null_indicators,
            coverage=coverage,
            as_of_time=latest_as_of_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest indicators for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest indicators"
        )
