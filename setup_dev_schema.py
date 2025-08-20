#!/usr/bin/env python3
"""
Setup dev schema and reinitialize database.
"""

import asyncio
import sys
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.base import engine, init_db
from app.data.indicator_catalog_loader import IndicatorCatalogLoader
from app.data.repositories import IndicatorCatalogRepository
from app.db.base import AsyncSessionLocal

logger = get_logger(__name__)

async def setup_dev_schema():
    """Setup dev schema and reinitialize database."""
    setup_logging()
    
    logger.info("Setting up dev schema...")
    
    try:
        async with engine.begin() as conn:
            # Create dev schema if it doesn't exist
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS dev"))
            logger.info("✅ Dev schema created/verified")
            
            # Set search path to dev
            await conn.execute(text("SET search_path TO dev, public"))
            logger.info("✅ Search path set to dev")
            
    except Exception as e:
        logger.error(f"❌ Failed to setup dev schema: {e}")
        return False
    
    return True

async def clean_old_tables():
    """Clean old tables from public schema."""
    try:
        async with engine.begin() as conn:
            # Drop tables from public schema if they exist
            await conn.execute(text("DROP TABLE IF EXISTS public.core_indicators_history CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS public.indicator_catalog CASCADE"))
            logger.info("✅ Cleaned old tables from public schema")
    except Exception as e:
        logger.error(f"❌ Failed to clean old tables: {e}")
        return False
    
    return True

async def init_dev_database():
    """Initialize database in dev schema."""
    try:
        # Initialize database tables in dev schema
        await init_db()
        logger.info("✅ Database tables initialized in dev schema")
        
        # Clean any existing data
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM core_indicators_history"))
            await session.execute(text("DELETE FROM indicator_catalog"))
            await session.commit()
            logger.info("✅ Cleaned existing data")
        
        # Import indicator catalog
        loader = IndicatorCatalogLoader()
        indicators = loader.load_from_csv()
        
        # Validate indicators
        errors = loader.validate_indicators(indicators)
        if errors:
            logger.error(f"Validation errors found: {errors}")
            return False
        
        async with AsyncSessionLocal() as session:
            repository = IndicatorCatalogRepository(session)
            
            # Import each indicator
            for indicator in indicators:
                await repository.upsert_indicator(indicator)
            
            await session.commit()
            logger.info(f"✅ Successfully imported {len(indicators)} indicators to dev schema")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize dev database: {e}")
        return False

async def verify_dev_setup():
    """Verify that dev schema setup is correct."""
    try:
        async with AsyncSessionLocal() as session:
            # Check current schema
            result = await session.execute(text("SELECT current_schema()"))
            current_schema = result.scalar()
            logger.info(f"Current schema: {current_schema}")
            
            # Check indicator catalog
            result = await session.execute(text("SELECT COUNT(*) FROM indicator_catalog"))
            catalog_count = result.scalar()
            
            # Check core indicators history
            result = await session.execute(text("SELECT COUNT(*) FROM core_indicators_history"))
            history_count = result.scalar()
            
            logger.info(f"Database verification:")
            logger.info(f"  - Schema: {current_schema}")
            logger.info(f"  - Indicator catalog: {catalog_count} records")
            logger.info(f"  - Core indicators history: {history_count} records")
            
            if current_schema == "dev" and catalog_count > 0:
                logger.info("✅ Dev schema setup completed successfully!")
                return True
            else:
                logger.error("❌ Dev schema setup verification failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to verify dev setup: {e}")
        return False

async def main():
    """Main setup function."""
    logger.info("Starting dev schema setup...")
    
    # Setup dev schema
    if not await setup_dev_schema():
        sys.exit(1)
    
    # Clean old tables
    if not await clean_old_tables():
        sys.exit(1)
    
    # Initialize dev database
    if not await init_dev_database():
        sys.exit(1)
    
    # Verify setup
    if not await verify_dev_setup():
        sys.exit(1)
    
    logger.info("🎉 Dev schema setup completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
