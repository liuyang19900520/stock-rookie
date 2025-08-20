import asyncio
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import get_rate_limiter
from app.core.retries import retry_async
from app.data.mapping import get_endpoint_url
from aiocache import cached

logger = get_logger(__name__)


class FMPAdapter:
    """FMP API adapter with rate limiting and caching."""
    
    def __init__(self):
        self.base_url = settings.fmp_base_url
        self.api_key = settings.fmp_api_key
        self.rate_limiter = get_rate_limiter()
        self.timeout = httpx.Timeout(30.0)
    
    async def _make_request(self, endpoint: str) -> Optional[List[Dict[str, Any]]]:
        """Make HTTP request to FMP API with rate limiting and retries."""
        url = f"{self.base_url}{endpoint}"
        params = {"apikey": self.api_key}
        
        # Apply rate limiting
        async with self.rate_limiter:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await retry_async(
                        client.get, url, params=params
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for {endpoint}: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Request error for {endpoint}: {e}")
                return None
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_quote(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch quote data for a symbol."""
        endpoint = get_endpoint_url("quote", symbol=symbol)
        return await self._make_request(endpoint)
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_profile(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch profile data for a symbol."""
        endpoint = get_endpoint_url("profile", symbol=symbol)
        return await self._make_request(endpoint)
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_key_metrics_ttm(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch key metrics TTM data for a symbol."""
        endpoint = get_endpoint_url("key-metrics-ttm", symbol=symbol)
        return await self._make_request(endpoint)
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_ratios_ttm(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch ratios TTM data for a symbol."""
        endpoint = get_endpoint_url("ratios-ttm", symbol=symbol)
        return await self._make_request(endpoint)
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_financial_growth(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch financial growth data for a symbol."""
        endpoint = get_endpoint_url("financial-growth", symbol=symbol)
        return await self._make_request(endpoint)
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_historical_price(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch historical price data for a symbol."""
        endpoint = get_endpoint_url("historical-price", symbol=symbol)
        return await self._make_request(endpoint)
    
    @cached(ttl=settings.cache_ttl, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
    async def fetch_dividends(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch dividends data for a symbol."""
        endpoint = get_endpoint_url("dividends", symbol=symbol)
        return await self._make_request(endpoint)
    
    async def fetch_technicals(
        self, 
        symbol: str, 
        indicator: str = "SMA", 
        period: int = 50
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch technical indicators data for a symbol."""
        endpoint = get_endpoint_url(
            "technicals", 
            symbol=symbol, 
            indicator=indicator, 
            period=str(period)
        )
        cache_key = f"technicals:{symbol}:{indicator}:{period}"
        
        # Custom caching for technical indicators
        @cached(ttl=settings.cache_ttl, key=cache_key)
        async def _fetch():
            return await self._make_request(endpoint)
        
        return await _fetch()
    
    async def fetch_by_source_api(
        self, 
        source_api: str, 
        symbol: str, 
        **kwargs: Any
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch data by source API alias."""
        method_map = {
            "quote": self.fetch_quote,
            "profile": self.fetch_profile,
            "key-metrics-ttm": self.fetch_key_metrics_ttm,
            "ratios-ttm": self.fetch_ratios_ttm,
            "financial-growth": self.fetch_financial_growth,
            "historical-price": self.fetch_historical_price,
            "dividends": self.fetch_dividends,
            "technicals": self.fetch_technicals,
        }
        
        if source_api not in method_map:
            logger.error(f"Unknown source API: {source_api}")
            return None
        
        method = method_map[source_api]
        if source_api == "technicals":
            return await method(symbol, **kwargs)
        else:
            return await method(symbol)


# Global FMP adapter instance
fmp_adapter = FMPAdapter()


def get_fmp_adapter() -> FMPAdapter:
    """Get the global FMP adapter instance."""
    return fmp_adapter
