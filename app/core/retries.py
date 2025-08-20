import asyncio
from typing import Any, Callable, TypeVar
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def create_retry_decorator() -> Callable:
    """Create a retry decorator with exponential backoff."""
    
    return retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(
            multiplier=settings.retry_delay_base,
            min=settings.retry_delay_base,
            max=settings.retry_delay_base * (2 ** (settings.max_retries - 1))
        ),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.HTTPStatusError
        )),
        before_sleep=before_sleep_log(logger, logger.warning),
        reraise=True
    )


# Global retry decorator
retry_on_network_error = create_retry_decorator()


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> Any:
    """Retry an async function with exponential backoff."""
    
    @retry_on_network_error
    async def _retry_func():
        return await func(*args, **kwargs)
    
    return await _retry_func()
