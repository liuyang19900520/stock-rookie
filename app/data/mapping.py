from typing import Any, Callable, Dict, Optional
from decimal import Decimal
from app.core.logging import get_logger

logger = get_logger(__name__)


# FMP API endpoint mappings
ENDPOINT_MAPPINGS = {
    "quote": "/quote/{symbol}",
    "profile": "/profile/{symbol}",
    "key-metrics-ttm": "/key-metrics-ttm/{symbol}",
    "ratios-ttm": "/ratios-ttm/{symbol}",
    "financial-growth": "/financial-growth/{symbol}",
    "historical-price": "/historical-price-full/{symbol}?serietype=line",
    "dividends": "/historical-price-full/stock_dividend/{symbol}",
    "technicals": "/technical_indicator/daily/{symbol}?type={indicator}&time_period={period}",
}


def get_endpoint_url(endpoint_alias: str, **kwargs: str) -> str:
    """Get FMP API endpoint URL for given alias."""
    if endpoint_alias not in ENDPOINT_MAPPINGS:
        raise ValueError(f"Unknown endpoint alias: {endpoint_alias}")
    
    url_template = ENDPOINT_MAPPINGS[endpoint_alias]
    return url_template.format(**kwargs)


# Field extraction functions
def extract_quote_field(data: Dict[str, Any], field: str) -> Optional[Any]:
    """Extract field from quote endpoint response."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    return data[0].get(field)


def extract_profile_field(data: Dict[str, Any], field: str) -> Optional[Any]:
    """Extract field from profile endpoint response."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    return data[0].get(field)


def extract_ttm_field(data: Dict[str, Any], field: str) -> Optional[Any]:
    """Extract field from TTM endpoints response."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    return data[0].get(field)


def extract_growth_field(data: Dict[str, Any], field: str) -> Optional[Any]:
    """Extract field from financial growth endpoint response."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    return data[0].get(field)


def extract_historical_field(data: Dict[str, Any], field: str) -> Optional[Any]:
    """Extract field from historical price endpoint response."""
    if not data or not isinstance(data, dict) or 'historical' not in data:
        return None
    
    historical = data['historical']
    if not historical or len(historical) == 0:
        return None
    
    # For historical data, we need to calculate based on the data
    if field == "volatility":
        # Calculate 90-day volatility from historical prices
        if len(historical) >= 90:
            prices = [float(record.get('close', 0)) for record in historical[:90]]
            if len(prices) >= 2:
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                import statistics
                return statistics.stdev(returns) * 100  # Convert to percentage
        return None
    elif field.startswith("priceChange"):
        # Calculate price changes for different periods
        if len(historical) >= 1:
            current_price = float(historical[0].get('close', 0))
            if current_price == 0:
                return None
            
            if field == "priceChange1m" and len(historical) >= 30:
                month_ago_price = float(historical[29].get('close', 0))
                return ((current_price - month_ago_price) / month_ago_price) * 100
            elif field == "priceChange3m" and len(historical) >= 90:
                quarter_ago_price = float(historical[89].get('close', 0))
                return ((current_price - quarter_ago_price) / quarter_ago_price) * 100
            elif field == "priceChange6m" and len(historical) >= 180:
                half_year_ago_price = float(historical[179].get('close', 0))
                return ((current_price - half_year_ago_price) / half_year_ago_price) * 100
            elif field == "priceChange12m" and len(historical) >= 365:
                year_ago_price = float(historical[364].get('close', 0))
                return ((current_price - year_ago_price) / year_ago_price) * 100
        
        return None
    elif field.startswith("distanceTo52w"):
        # Calculate distance to 52-week high/low
        if len(historical) >= 365:
            prices = [float(record.get('close', 0)) for record in historical[:365]]
            if prices:
                high_52w = max(prices)
                low_52w = min(prices)
                current_price = float(historical[0].get('close', 0))
                
                if field == "distanceTo52wHigh":
                    return ((high_52w - current_price) / current_price) * 100
                elif field == "distanceTo52wLow":
                    return ((current_price - low_52w) / current_price) * 100
        
        return None
    
    return None


def extract_technical_field(data: Dict[str, Any], field: str) -> Optional[Any]:
    """Extract field from technical indicators endpoint response."""
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    return data[0].get(field)


# Value conversion functions
def convert_percentage(value: Any) -> Optional[Decimal]:
    """Convert percentage string to decimal (e.g., '12.34%' -> 0.1234)."""
    if value is None:
        return None
    
    try:
        if isinstance(value, str):
            if value.endswith('%'):
                return Decimal(value.rstrip('%')) / 100
            return Decimal(value)
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        else:
            return None
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert percentage value: {value}")
        return None


def convert_currency(value: Any) -> Optional[Decimal]:
    """Convert currency value to decimal."""
    if value is None:
        return None
    
    try:
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            return Decimal(cleaned)
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        else:
            return None
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert currency value: {value}")
        return None


def convert_ratio(value: Any) -> Optional[Decimal]:
    """Convert ratio value to decimal."""
    if value is None:
        return None
    
    try:
        if isinstance(value, str):
            return Decimal(value)
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        else:
            return None
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert ratio value: {value}")
        return None


def convert_count(value: Any) -> Optional[Decimal]:
    """Convert count value to decimal."""
    if value is None:
        return None
    
    try:
        if isinstance(value, str):
            # Remove commas
            cleaned = value.replace(',', '').strip()
            return Decimal(cleaned)
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        else:
            return None
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert count value: {value}")
        return None


# Indicator field mappings - Updated based on actual FMP API fields
INDICATOR_FIELD_MAPPINGS: Dict[str, Dict[str, Any]] = {
    # Quote endpoint indicators
    "price": {
        "source_api": "quote",
        "field": "price",
        "extractor": extract_quote_field,
        "converter": convert_currency,
    },
    "market_cap": {
        "source_api": "quote",
        "field": "marketCap",
        "extractor": extract_quote_field,
        "converter": convert_currency,
    },
    "enterprise_value": {
        "source_api": "key-metrics-ttm",
        "field": "enterpriseValueTTM",
        "extractor": extract_ttm_field,
        "converter": convert_currency,
    },
    "beta": {
        "source_api": "profile",
        "field": "beta",
        "extractor": extract_profile_field,
        "converter": convert_ratio,
    },
    
    # Profile endpoint indicators
    "week52_high": {
        "source_api": "profile",
        "field": "range",
        "extractor": extract_profile_field,
        "converter": lambda x: convert_currency(x.split('-')[1]) if x and '-' in x else None,
    },
    "week52_low": {
        "source_api": "profile",
        "field": "range",
        "extractor": extract_profile_field,
        "converter": lambda x: convert_currency(x.split('-')[0]) if x and '-' in x else None,
    },
    "avg_volume_90d": {
        "source_api": "profile",
        "field": "volAvg",
        "extractor": extract_profile_field,
        "converter": convert_count,
    },
    
    # Key metrics TTM indicators
    "pe_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "peRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "pe_forward": {
        "source_api": "quote",
        "field": "pe",
        "extractor": extract_quote_field,
        "converter": convert_ratio,
    },
    "pb": {
        "source_api": "key-metrics-ttm",
        "field": "pbRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "ps_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "priceToSalesRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "ev_ebitda": {
        "source_api": "key-metrics-ttm",
        "field": "enterpriseValueOverEBITDATTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "ev_ebit": {
        "source_api": "key-metrics-ttm",
        "field": "evToOperatingCashFlowTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "earnings_yield_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "earningsYieldTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "fcf_yield_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "freeCashFlowYieldTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "dividend_yield_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "dividendYieldTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "net_debt_ebitda": {
        "source_api": "key-metrics-ttm",
        "field": "netDebtToEBITDATTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "dividend_yield_current": {
        "source_api": "key-metrics-ttm",
        "field": "dividendYieldTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "dividend_cagr_3y": {
        "source_api": "financial-growth",
        "field": "threeYDividendperShareGrowthPerShare",
        "extractor": extract_growth_field,
        "converter": convert_percentage,
    },
    
    # Ratios TTM indicators
    "payout_ratio_ttm": {
        "source_api": "ratios-ttm",
        "field": "payoutRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "roe_ttm": {
        "source_api": "ratios-ttm",
        "field": "returnOnEquityTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "roa_ttm": {
        "source_api": "ratios-ttm",
        "field": "returnOnAssetsTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "roic_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "roicTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "gross_margin_ttm": {
        "source_api": "ratios-ttm",
        "field": "grossProfitMarginTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "operating_margin_ttm": {
        "source_api": "ratios-ttm",
        "field": "operatingProfitMarginTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "net_margin_ttm": {
        "source_api": "ratios-ttm",
        "field": "netProfitMarginTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "fcf_margin_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "freeCashFlowYieldTTM",
        "extractor": extract_ttm_field,
        "converter": convert_percentage,
    },
    "cashflow_quality_ttm": {
        "source_api": "key-metrics-ttm",
        "field": "operatingCashFlowPerShareTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "asset_turnover_ttm": {
        "source_api": "ratios-ttm",
        "field": "assetTurnoverTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "interest_coverage_ttm": {
        "source_api": "ratios-ttm",
        "field": "interestCoverageTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "debt_equity": {
        "source_api": "ratios-ttm",
        "field": "debtEquityRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "current_ratio": {
        "source_api": "ratios-ttm",
        "field": "currentRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "quick_ratio": {
        "source_api": "ratios-ttm",
        "field": "quickRatioTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "altman_z": {
        "source_api": "ratios-ttm",
        "field": "altmanZScoreTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    "piotroski_f": {
        "source_api": "ratios-ttm",
        "field": "piotroskiScoreTTM",
        "extractor": extract_ttm_field,
        "converter": convert_ratio,
    },
    
    # Financial growth indicators
    "revenue_yoy": {
        "source_api": "financial-growth",
        "field": "revenueGrowth",
        "extractor": extract_growth_field,
        "converter": convert_percentage,
    },
    "eps_yoy": {
        "source_api": "financial-growth",
        "field": "epsgrowth",
        "extractor": extract_growth_field,
        "converter": convert_percentage,
    },
    "revenue_cagr_3y": {
        "source_api": "financial-growth",
        "field": "threeYRevenueGrowthPerShare",
        "extractor": extract_growth_field,
        "converter": convert_percentage,
    },
    "eps_cagr_3y": {
        "source_api": "financial-growth",
        "field": "threeYNetIncomeGrowthPerShare",
        "extractor": extract_growth_field,
        "converter": convert_percentage,
    },
    "fcf_yoy": {
        "source_api": "financial-growth",
        "field": "freeCashFlowGrowth",
        "extractor": extract_growth_field,
        "converter": convert_percentage,
    },
    
    # Historical price indicators (calculated from historical data)
    "volatility_90d": {
        "source_api": "historical-price",
        "field": "volatility",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    "price_change_1m": {
        "source_api": "historical-price",
        "field": "priceChange1m",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    "price_change_3m": {
        "source_api": "historical-price",
        "field": "priceChange3m",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    "price_change_6m": {
        "source_api": "historical-price",
        "field": "priceChange6m",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    "price_change_12m": {
        "source_api": "historical-price",
        "field": "priceChange12m",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    "distance_to_52w_high": {
        "source_api": "historical-price",
        "field": "distanceTo52wHigh",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    "distance_to_52w_low": {
        "source_api": "historical-price",
        "field": "distanceTo52wLow",
        "extractor": extract_historical_field,
        "converter": convert_percentage,
    },
    
    # Technical indicators (from quote endpoint for now)
    "sma50": {
        "source_api": "quote",
        "field": "priceAvg50",
        "extractor": extract_quote_field,
        "converter": convert_currency,
    },
    "sma200": {
        "source_api": "quote",
        "field": "priceAvg200",
        "extractor": extract_quote_field,
        "converter": convert_currency,
    },
    "rsi14": {
        "source_api": "technicals",
        "field": "rsi14",
        "extractor": extract_technical_field,
        "converter": convert_ratio,
    },
}


def get_indicator_mapping(indicator_id: str) -> Optional[Dict[str, Any]]:
    """Get mapping configuration for an indicator."""
    return INDICATOR_FIELD_MAPPINGS.get(indicator_id)


def extract_indicator_value(
    data: Dict[str, Any], 
    indicator_id: str
) -> Optional[Decimal]:
    """Extract and convert indicator value from API response."""
    mapping = get_indicator_mapping(indicator_id)
    if not mapping:
        logger.warning(f"No mapping found for indicator: {indicator_id}")
        return None
    
    try:
        raw_value = mapping["extractor"](data, mapping["field"])
        if raw_value is None:
            return None
        
        return mapping["converter"](raw_value)
    except Exception as e:
        logger.error(f"Error extracting value for {indicator_id}: {e}")
        return None


def get_indicators_by_source_api(source_api: str) -> list[str]:
    """Get list of indicator IDs for a given source API."""
    return [
        indicator_id for indicator_id, mapping in INDICATOR_FIELD_MAPPINGS.items()
        if mapping["source_api"] == source_api
    ]
