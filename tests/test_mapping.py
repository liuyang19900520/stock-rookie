import pytest
from decimal import Decimal
from app.data.mapping import (
    get_endpoint_url,
    convert_percentage,
    convert_currency,
    convert_ratio,
    convert_count,
    extract_indicator_value,
    get_indicators_by_source_api
)


class TestMapping:
    """Test mapping functionality."""
    
    def test_get_endpoint_url(self):
        """Test endpoint URL generation."""
        # Test valid endpoints
        assert get_endpoint_url("quote", symbol="AAPL") == "/quote/AAPL"
        assert get_endpoint_url("profile", symbol="MSFT") == "/profile/MSFT"
        assert get_endpoint_url("key-metrics-ttm", symbol="GOOGL") == "/key-metrics-ttm/GOOGL"
        
        # Test invalid endpoint
        with pytest.raises(ValueError):
            get_endpoint_url("invalid_endpoint", symbol="AAPL")
    
    def test_convert_percentage(self):
        """Test percentage conversion."""
        # Test percentage strings
        assert convert_percentage("12.34%") == Decimal("0.1234")
        assert convert_percentage("0.5%") == Decimal("0.005")
        assert convert_percentage("100%") == Decimal("1.0")
        
        # Test decimal strings
        assert convert_percentage("0.1234") == Decimal("0.1234")
        assert convert_percentage("1.0") == Decimal("1.0")
        
        # Test numbers
        assert convert_percentage(0.1234) == Decimal("0.1234")
        assert convert_percentage(12.34) == Decimal("12.34")
        
        # Test None and invalid values
        assert convert_percentage(None) is None
        assert convert_percentage("invalid") is None
        assert convert_percentage("") is None
    
    def test_convert_currency(self):
        """Test currency conversion."""
        # Test currency strings
        assert convert_currency("$1,234.56") == Decimal("1234.56")
        assert convert_currency("$100") == Decimal("100")
        assert convert_currency("1,000,000") == Decimal("1000000")
        
        # Test numbers
        assert convert_currency(1234.56) == Decimal("1234.56")
        assert convert_currency(100) == Decimal("100")
        
        # Test None and invalid values
        assert convert_currency(None) is None
        assert convert_currency("invalid") is None
        assert convert_currency("") is None
    
    def test_convert_ratio(self):
        """Test ratio conversion."""
        # Test valid ratios
        assert convert_ratio("1.5") == Decimal("1.5")
        assert convert_ratio("0.75") == Decimal("0.75")
        assert convert_ratio(2.5) == Decimal("2.5")
        
        # Test None and invalid values
        assert convert_ratio(None) is None
        assert convert_ratio("invalid") is None
        assert convert_ratio("") is None
    
    def test_convert_count(self):
        """Test count conversion."""
        # Test counts with commas
        assert convert_count("1,234,567") == Decimal("1234567")
        assert convert_count("100") == Decimal("100")
        assert convert_count(50000) == Decimal("50000")
        
        # Test None and invalid values
        assert convert_count(None) is None
        assert convert_count("invalid") is None
        assert convert_count("") is None
    
    def test_extract_indicator_value(self):
        """Test indicator value extraction."""
        # Mock API response data
        mock_data = [
            {
                "price": 150.25,
                "marketCap": 2500000000000,
                "beta": 1.15,
                "peRatioTTM": 25.5,
                "roeTTM": 0.18
            }
        ]
        
        # Test valid extractions
        assert extract_indicator_value(mock_data, "price") == Decimal("150.25")
        assert extract_indicator_value(mock_data, "market_cap") == Decimal("2500000000000")
        assert extract_indicator_value(mock_data, "beta") == Decimal("1.15")
        assert extract_indicator_value(mock_data, "pe_ttm") == Decimal("25.5")
        assert extract_indicator_value(mock_data, "roe_ttm") == Decimal("0.18")
        
        # Test missing indicator
        assert extract_indicator_value(mock_data, "nonexistent") is None
        
        # Test empty data
        assert extract_indicator_value([], "price") is None
        assert extract_indicator_value(None, "price") is None
    
    def test_get_indicators_by_source_api(self):
        """Test getting indicators by source API."""
        quote_indicators = get_indicators_by_source_api("quote")
        assert len(quote_indicators) > 0
        assert "price" in quote_indicators
        assert "market_cap" in quote_indicators
        
        profile_indicators = get_indicators_by_source_api("profile")
        assert len(profile_indicators) > 0
        assert "week52_high" in profile_indicators
        assert "week52_low" in profile_indicators
        
        # Test non-existent API
        invalid_indicators = get_indicators_by_source_api("invalid_api")
        assert len(invalid_indicators) == 0
