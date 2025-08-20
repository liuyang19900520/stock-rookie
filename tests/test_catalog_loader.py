import pytest
from app.data.indicator_catalog_loader import IndicatorCatalogLoader
from app.schemas.catalog import IndicatorCatalogCreate


class TestIndicatorCatalogLoader:
    """Test indicator catalog loader functionality."""
    
    def test_load_from_csv(self):
        """Test loading indicators from CSV file."""
        loader = IndicatorCatalogLoader()
        indicators = loader.load_from_csv()
        
        # Should load indicators
        assert len(indicators) > 0
        
        # All should be IndicatorCatalogCreate instances
        for indicator in indicators:
            assert isinstance(indicator, IndicatorCatalogCreate)
        
        # Check some required fields
        for indicator in indicators:
            assert indicator.indicator_id
            assert indicator.description
            assert indicator.unit
            assert indicator.direction
            assert indicator.source_api
            assert indicator.frequency
            assert indicator.is_core is True
    
    def test_validate_indicators(self):
        """Test indicator validation."""
        loader = IndicatorCatalogLoader()
        
        # Valid indicators
        valid_indicators = [
            IndicatorCatalogCreate(
                indicator_id="test1",
                description="Test indicator 1",
                unit="USD",
                direction="higher_is_better",
                source_api="quote",
                frequency="daily",
                historical=True,
                trend_ready=True,
                is_core=True,
                active=True
            )
        ]
        
        errors = loader.validate_indicators(valid_indicators)
        assert len(errors) == 0
        
        # Invalid indicators
        invalid_indicators = [
            IndicatorCatalogCreate(
                indicator_id="",  # Empty ID
                description="Test indicator",
                unit="INVALID_UNIT",  # Invalid unit
                direction="invalid_direction",  # Invalid direction
                source_api="invalid_api",  # Invalid API
                frequency="invalid_frequency",  # Invalid frequency
                historical=True,
                trend_ready=True,
                is_core=True,
                active=True
            )
        ]
        
        errors = loader.validate_indicators(invalid_indicators)
        assert len(errors) > 0
        assert any("Missing indicator_id" in error for error in errors)
        assert any("Invalid unit" in error for error in errors)
        assert any("Invalid direction" in error for error in errors)
        assert any("Invalid source_api" in error for error in errors)
        assert any("Invalid frequency" in error for error in errors)
