from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import IndicatorCatalog, CoreIndicatorsHistory
from app.schemas.catalog import IndicatorCatalogCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


class IndicatorCatalogRepository:
    """Repository for indicator catalog operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_core_indicators(self) -> List[IndicatorCatalog]:
        """Get all active core indicators."""
        stmt = select(IndicatorCatalog).where(
            and_(
                IndicatorCatalog.is_core == True,
                IndicatorCatalog.active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_indicator_id(self, indicator_id: str) -> Optional[IndicatorCatalog]:
        """Get indicator by ID."""
        stmt = select(IndicatorCatalog).where(
            IndicatorCatalog.indicator_id == indicator_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def upsert_indicator(self, indicator_data: IndicatorCatalogCreate) -> IndicatorCatalog:
        """Upsert indicator catalog entry."""
        existing = await self.get_by_indicator_id(indicator_data.indicator_id)
        
        if existing:
            # Update existing
            for field, value in indicator_data.model_dump().items():
                setattr(existing, field, value)
            existing.updated_at = datetime.utcnow()
            indicator = existing
        else:
            # Create new
            indicator = IndicatorCatalog(**indicator_data.model_dump())
            self.session.add(indicator)
        
        await self.session.commit()
        await self.session.refresh(indicator)
        return indicator
    
    async def bulk_upsert_indicators(
        self, 
        indicators: List[IndicatorCatalogCreate]
    ) -> List[IndicatorCatalog]:
        """Bulk upsert indicators."""
        results = []
        for indicator_data in indicators:
            result = await self.upsert_indicator(indicator_data)
            results.append(result)
        return results


class CoreIndicatorsRepository:
    """Repository for core indicators history operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def upsert_indicator_value(
        self,
        stock_id: str,
        date: date,
        indicator_id: str,
        value: Optional[Decimal] = None,
        currency: Optional[str] = None,
        source: Optional[str] = None,
        null_reason: Optional[str] = None
    ) -> CoreIndicatorsHistory:
        """Upsert a single indicator value."""
        
        # Check if record exists
        stmt = select(CoreIndicatorsHistory).where(
            and_(
                CoreIndicatorsHistory.stock_id == stock_id,
                CoreIndicatorsHistory.date == date,  # date is already a date object
                CoreIndicatorsHistory.indicator_id == indicator_id
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            existing.value = value
            existing.currency = currency
            existing.source = source
            existing.null_reason = null_reason
            existing.as_of_time = datetime.utcnow()
            record = existing
        else:
            # Create new record
            record = CoreIndicatorsHistory(
                stock_id=stock_id,
                date=date,
                indicator_id=indicator_id,
                value=value,
                currency=currency,
                source=source,
                null_reason=null_reason
            )
            self.session.add(record)
        
        await self.session.commit()
        await self.session.refresh(record)
        return record
    
    async def bulk_upsert_indicators(
        self,
        stock_id: str,
        date: date,
        indicators_data: List[Dict]
    ) -> List[CoreIndicatorsHistory]:
        """Bulk upsert indicator values for a stock on a specific date."""
        records = []
        
        for data in indicators_data:
            record = await self.upsert_indicator_value(
                stock_id=stock_id,
                date=date,
                indicator_id=data["indicator_id"],
                value=data.get("value"),
                currency=data.get("currency"),
                source=data.get("source"),
                null_reason=data.get("null_reason")
            )
            records.append(record)
        
        return records
    
    async def get_latest_indicators(
        self, 
        stock_id: str
    ) -> Optional[Dict[str, CoreIndicatorsHistory]]:
        """Get latest indicators for a stock."""
        
        # Get the latest date for this stock
        latest_date_stmt = select(func.max(CoreIndicatorsHistory.date)).where(
            CoreIndicatorsHistory.stock_id == stock_id
        )
        result = await self.session.execute(latest_date_stmt)
        latest_date = result.scalar_one_or_none()
        
        if not latest_date:
            return None
        
        # Get all indicators for the latest date
        stmt = select(CoreIndicatorsHistory).where(
            and_(
                CoreIndicatorsHistory.stock_id == stock_id,
                CoreIndicatorsHistory.date == latest_date
            )
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        
        # Convert to dictionary
        indicators = {}
        for record in records:
            indicators[record.indicator_id] = record
        
        return indicators
    
    async def get_indicators_by_date_range(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
        indicator_ids: Optional[List[str]] = None
    ) -> List[CoreIndicatorsHistory]:
        """Get indicators for a stock within a date range."""
        
        conditions = [
            CoreIndicatorsHistory.stock_id == stock_id,
            CoreIndicatorsHistory.date >= start_date,
            CoreIndicatorsHistory.date <= end_date
        ]
        
        if indicator_ids:
            conditions.append(
                CoreIndicatorsHistory.indicator_id.in_(indicator_ids)
            )
        
        stmt = select(CoreIndicatorsHistory).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_coverage_stats(
        self,
        stock_id: str,
        date: date
    ) -> Dict[str, int]:
        """Get coverage statistics for a stock on a specific date."""
        
        stmt = select(
            func.count(CoreIndicatorsHistory.indicator_id).label("total"),
            func.count(CoreIndicatorsHistory.value).label("non_null")
        ).where(
            and_(
                CoreIndicatorsHistory.stock_id == stock_id,
                CoreIndicatorsHistory.date == date
            )
        )
        
        result = await self.session.execute(stmt)
        row = result.fetchone()
        
        return {
            "total": row.total or 0,
            "non_null": row.non_null or 0
        }
