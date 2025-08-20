from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.data.repositories import IndicatorCatalogRepository
from app.data.indicator_catalog_loader import IndicatorCatalogLoader
from app.schemas.catalog import (
    IndicatorCatalog as IndicatorCatalogSchema,
    IndicatorCatalogResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/indicators", tags=["catalog"])


@router.get("/catalog", response_model=IndicatorCatalogResponse)
async def get_indicator_catalog(
    is_core: bool = True,
    db: AsyncSession = Depends(get_db)
) -> IndicatorCatalogResponse:
    """Get indicator catalog."""
    try:
        repo = IndicatorCatalogRepository(db)
        
        if is_core:
            indicators = await repo.get_all_core_indicators()
        else:
            # For now, only support core indicators
            indicators = await repo.get_all_core_indicators()
        
        return IndicatorCatalogResponse(
            indicators=[IndicatorCatalogSchema.model_validate(indicator) for indicator in indicators],
            total=len(indicators),
            is_core_only=is_core
        )
    
    except Exception as e:
        logger.error(f"Error getting indicator catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve indicator catalog"
        )


@router.post("/catalog/import")
async def import_indicator_catalog(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Import indicator catalog from CSV file."""
    try:
        # Load indicators from CSV
        loader = IndicatorCatalogLoader()
        indicators = loader.load_from_csv()
        
        if not indicators:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No indicators found in CSV file"
            )
        
        # Validate indicators
        errors = loader.validate_indicators(indicators)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {errors}"
            )
        
        # Import to database
        repo = IndicatorCatalogRepository(db)
        imported_indicators = await repo.bulk_upsert_indicators(indicators)
        
        logger.info(f"Successfully imported {len(imported_indicators)} indicators")
        
        return {
            "message": "Indicator catalog imported successfully",
            "imported_count": len(imported_indicators),
            "total_indicators": len(indicators)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing indicator catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import indicator catalog"
        )
