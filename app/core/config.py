from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # FMP API Configuration
    fmp_api_key: str = Field(..., description="FMP API key (required)")
    fmp_base_url: str = Field(
        default="https://financialmodelingprep.com/api/v3",
        description="FMP API base URL"
    )
    
    # Database Configuration
    db_url: str = Field(
        default="postgresql+asyncpg://username:password@your-database-host:5432/database_name",
        description="Database connection URL"
    )
    
    # Rate Limiting
    rate_limit_rps: int = Field(
        default=3,
        description="Rate limit requests per second"
    )
    rate_limit_burst: int = Field(
        default=6,
        description="Rate limit burst capacity"
    )
    
    # Timezone Configuration
    timezone: str = Field(
        default="Asia/Tokyo",
        description="Application timezone"
    )
    
    # Scheduling Configuration
    ingest_schedule_cron: str = Field(
        default="0 18 * * *",
        description="Cron expression for daily ingest schedule (Tokyo time 18:00)"
    )
    
    # Cache Configuration
    cache_ttl: int = Field(
        default=300,  # 5 minutes
        description="Cache TTL in seconds"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for API calls"
    )
    retry_delay_base: float = Field(
        default=0.5,
        description="Base delay for exponential backoff (seconds)"
    )
    
    # Coverage Threshold
    coverage_threshold: float = Field(
        default=0.8,
        description="Minimum coverage threshold for ingest success (80%)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
