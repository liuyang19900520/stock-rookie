from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class IndicatorCatalog(Base):
    """Indicator catalog table."""
    
    __tablename__ = "indicator_catalog"
    
    indicator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    direction: Mapped[str] = mapped_column(String(24), nullable=False)
    source_api: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    historical: Mapped[bool] = mapped_column(Boolean, nullable=False)
    trend_ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )


class CoreIndicatorsHistory(Base):
    """Core indicators history table."""
    
    __tablename__ = "core_indicators_history"
    
    stock_id: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    indicator_id: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(30, 10), nullable=True
    )
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    as_of_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    null_reason: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True
    )
    
    __table_args__ = (
        # Primary key
        PrimaryKeyConstraint('stock_id', 'date', 'indicator_id'),
        # Indexes
        Index("idx_core_hist__stock_date", 'stock_id', 'date'),
        Index("idx_core_hist__indicator_date", 'indicator_id', 'date'),
    )
