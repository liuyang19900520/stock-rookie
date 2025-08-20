from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request schema for core indicators ingest."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    symbols: list[str] = Field(..., description="List of stock symbols to ingest")
    date: Optional[date] = Field(default=None, description="Target date for ingest (defaults to current date)")


class IngestResult(BaseModel):
    """Result for a single symbol ingest."""
    
    symbol: str
    date: date
    total_indicators: int
    non_null_indicators: int
    coverage: float
    duration_ms: int
    success: bool
    error: Optional[str] = None


class IngestResponse(BaseModel):
    """Response schema for core indicators ingest."""
    
    results: list[IngestResult]
    total_symbols: int
    successful_symbols: int
    failed_symbols: int
    overall_duration_ms: int
    timestamp: datetime


class CoreIndicatorValue(BaseModel):
    """Schema for a single core indicator value."""
    
    indicator_id: str
    value: Optional[Decimal] = None
    unit: str
    currency: Optional[str] = None
    date: date
    source: Optional[str] = None
    null_reason: Optional[str] = None


class CoreIndicatorsLatest(BaseModel):
    """Schema for latest core indicators for a ticker."""
    
    symbol: str
    date: date
    indicators: dict[str, CoreIndicatorValue]
    total_indicators: int
    non_null_indicators: int
    coverage: float
    as_of_time: datetime
