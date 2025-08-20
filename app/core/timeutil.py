from datetime import date, datetime, timezone
from typing import Optional
import pytz
from app.core.config import settings


# Get timezone
TZ = pytz.timezone(settings.timezone)


def get_current_date() -> date:
    """Get current date in application timezone."""
    return datetime.now(TZ).date()


def get_current_datetime() -> datetime:
    """Get current datetime in application timezone."""
    return datetime.now(TZ)


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def format_date(d: date) -> str:
    """Format date to YYYY-MM-DD string."""
    return d.strftime("%Y-%m-%d")


def to_utc(dt: datetime) -> datetime:
    """Convert timezone-aware datetime to UTC."""
    if dt.tzinfo is None:
        dt = TZ.localize(dt)
    return dt.astimezone(timezone.utc)


def from_utc(dt: datetime) -> datetime:
    """Convert UTC datetime to application timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ)


def get_effective_date(
    api_date: Optional[str],
    fallback_date: Optional[date] = None
) -> date:
    """Get effective date for indicators.
    
    For daily indicators: use trading date from API response
    For TTM/quarterly: use date from API response or fallback
    """
    if api_date:
        try:
            return parse_date(api_date)
        except ValueError:
            pass
    
    if fallback_date:
        return fallback_date
    
    return get_current_date()


def is_business_day(d: date) -> bool:
    """Check if date is a business day (Monday-Friday)."""
    return d.weekday() < 5  # 0=Monday, 6=Sunday
