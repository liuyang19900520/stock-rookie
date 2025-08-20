import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import init_db, close_db
from app.jobs.scheduler import get_scheduler
from app.api.routes_catalog import router as catalog_router
from app.api.routes_ingest import router as ingest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    
    # Initialize database
    await init_db()
    
    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Core Indicators Service",
    description="Service for collecting and storing core financial indicators",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(catalog_router)
app.include_router(ingest_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Core Indicators Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/config")
async def get_config():
    """Get application configuration (for debugging)."""
    return {
        "fmp_base_url": settings.fmp_base_url,
        "rate_limit_rps": settings.rate_limit_rps,
        "rate_limit_burst": settings.rate_limit_burst,
        "timezone": settings.timezone,
        "ingest_schedule_cron": settings.ingest_schedule_cron,
        "cache_ttl": settings.cache_ttl,
        "max_retries": settings.max_retries,
        "coverage_threshold": settings.coverage_threshold
    }
