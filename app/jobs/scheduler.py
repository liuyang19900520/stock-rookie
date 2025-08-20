import asyncio
from datetime import date
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import AsyncSessionLocal
from app.data.ingest_service import IngestService
from app.data.repositories import IndicatorCatalogRepository

logger = get_logger(__name__)


class JobScheduler:
    """Scheduler for automated jobs."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self) -> None:
        """Setup scheduled jobs."""
        
        # Daily core indicators ingest
        self.scheduler.add_job(
            func=self._daily_ingest_job,
            trigger=CronTrigger.from_crontab(settings.ingest_schedule_cron),
            id="daily_core_ingest",
            name="Daily Core Indicators Ingest",
            replace_existing=True
        )
        
        logger.info("Scheduled jobs configured")
    
    async def _daily_ingest_job(self) -> None:
        """Daily job to ingest core indicators for tracked symbols."""
        logger.info("Starting daily core indicators ingest job")
        
        try:
            # Get tracked symbols (for now, use a predefined list)
            # In a real implementation, this would come from a configuration or database
            tracked_symbols = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
                "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "BAC",
                "ADBE", "CRM", "ABT", "KO", "PEP", "TMO", "AVGO", "COST", "DHR",
                "ACN", "NEE", "LLY", "TXN", "HON", "UNP", "LOW", "UPS", "IBM",
                "RTX", "QCOM", "CAT", "GS", "MS", "SPGI", "AMGN", "T", "INTC",
                "VZ", "CVX", "WMT", "MRK", "PFE"
            ]
            
            # Perform ingest
            async with AsyncSessionLocal() as session:
                service = IngestService(session)
                results = await service.ingest_multiple_symbols(
                    symbols=tracked_symbols,
                    target_date=date.today()
                )
            
            # Log results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            logger.info(
                f"Daily ingest completed: {len(results)} symbols, "
                f"{successful} successful, {failed} failed"
            )
            
        except Exception as e:
            logger.error(f"Error in daily ingest job: {e}")
    
    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Job scheduler started")
    
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Job scheduler shutdown")


# Global scheduler instance
scheduler = JobScheduler()


def get_scheduler() -> JobScheduler:
    """Get the global scheduler instance."""
    return scheduler
