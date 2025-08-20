import asyncio
from typing import Optional
from aiolimiter import AsyncLimiter
from app.core.config import settings


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self):
        self.limiter = AsyncLimiter(
            max_rate=settings.rate_limit_rps,
            time_period=1.0
        )
    
    async def acquire(self) -> None:
        """Acquire a token from the rate limiter."""
        await self.limiter.acquire()
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return rate_limiter
