import logging
import sys
from typing import Any
from app.core.config import settings


def setup_logging() -> None:
    """Setup application logging configuration."""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Setup file handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class IngestLogger:
    """Specialized logger for ingest operations with structured logging."""
    
    def __init__(self, symbol: str, date: str):
        self.symbol = symbol
        self.date = date
        self.logger = get_logger("ingest")
    
    def log_start(self) -> None:
        """Log ingest start."""
        self.logger.info(
            f"Starting ingest for {self.symbol} on {self.date}"
        )
    
    def log_completion(
        self, 
        total: int, 
        non_null: int, 
        coverage: float, 
        duration_ms: int
    ) -> None:
        """Log ingest completion with metrics."""
        self.logger.info(
            f"Ingest completed: {self.symbol}, {self.date}, "
            f"total={total}, non_null={non_null}, "
            f"coverage={coverage:.2%}, duration_ms={duration_ms}"
        )
    
    def log_error(self, error: str) -> None:
        """Log ingest error."""
        self.logger.error(
            f"Ingest error for {self.symbol} on {self.date}: {error}"
        )
    
    def log_api_error(self, endpoint: str, error: str) -> None:
        """Log API error for specific endpoint."""
        self.logger.warning(
            f"API error for {self.symbol} on {self.date} "
            f"endpoint={endpoint}: {error}"
        )
