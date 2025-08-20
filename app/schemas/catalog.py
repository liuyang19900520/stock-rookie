from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class IndicatorCatalogBase(BaseModel):
    """Base indicator catalog schema."""
    
    indicator_id: str = Field(..., description="Unique indicator identifier")
    description: str = Field(..., description="Indicator description")
    unit: str = Field(..., description="Unit of measurement")
    direction: str = Field(..., description="Direction (higher_is_better, lower_is_better, range)")
    source_api: str = Field(..., description="Source API endpoint alias")
    frequency: str = Field(..., description="Update frequency (daily, quarterly, annual)")
    historical: bool = Field(..., description="Whether historical data is available")
    trend_ready: bool = Field(..., description="Whether ready for trend analysis")
    is_core: bool = Field(..., description="Whether this is a core indicator")
    active: bool = Field(default=True, description="Whether indicator is active")


class IndicatorCatalogCreate(IndicatorCatalogBase):
    """Schema for creating indicator catalog entry."""
    pass


class IndicatorCatalogUpdate(BaseModel):
    """Schema for updating indicator catalog entry."""
    
    description: Optional[str] = None
    unit: Optional[str] = None
    direction: Optional[str] = None
    source_api: Optional[str] = None
    frequency: Optional[str] = None
    historical: Optional[bool] = None
    trend_ready: Optional[bool] = None
    is_core: Optional[bool] = None
    active: Optional[bool] = None


class IndicatorCatalog(IndicatorCatalogBase):
    """Complete indicator catalog schema with timestamps."""
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IndicatorCatalogResponse(BaseModel):
    """Response schema for indicator catalog."""
    
    indicators: list[IndicatorCatalog]
    total: int
    is_core_only: bool = True