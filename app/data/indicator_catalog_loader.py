import csv
import os
from typing import List
from app.schemas.catalog import IndicatorCatalogCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


class IndicatorCatalogLoader:
    """Loader for indicator catalog from CSV file."""
    
    def __init__(self, csv_path: str = "app/static/indicator_catalog_core.csv"):
        self.csv_path = csv_path
    
    def load_from_csv(self) -> List[IndicatorCatalogCreate]:
        """Load indicator catalog from CSV file."""
        indicators = []
        
        if not os.path.exists(self.csv_path):
            logger.error(f"CSV file not found: {self.csv_path}")
            return indicators
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    try:
                        indicator = IndicatorCatalogCreate(
                            indicator_id=row['indicator_id'],
                            description=row['description'],
                            unit=row['unit'],
                            direction=row['direction'],
                            source_api=row['source_api'],
                            frequency=row['frequency'],
                            historical=row['historical'].lower() == 'true',
                            trend_ready=row['trend_ready'].lower() == 'true',
                            is_core=row['is_core'].lower() == 'true',
                            active=True  # Default to active
                        )
                        indicators.append(indicator)
                    except Exception as e:
                        logger.error(f"Error parsing row {row}: {e}")
                        continue
                
                logger.info(f"Loaded {len(indicators)} indicators from CSV")
                return indicators
                
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return indicators
    
    def validate_indicators(self, indicators: List[IndicatorCatalogCreate]) -> List[str]:
        """Validate indicators and return list of errors."""
        errors = []
        
        # Check for required fields
        for indicator in indicators:
            if not indicator.indicator_id:
                errors.append(f"Missing indicator_id for indicator: {indicator.description}")
            
            if not indicator.description:
                errors.append(f"Missing description for indicator: {indicator.indicator_id}")
            
            if not indicator.unit:
                errors.append(f"Missing unit for indicator: {indicator.indicator_id}")
            
            if not indicator.direction:
                errors.append(f"Missing direction for indicator: {indicator.indicator_id}")
            
            if not indicator.source_api:
                errors.append(f"Missing source_api for indicator: {indicator.indicator_id}")
            
            if not indicator.frequency:
                errors.append(f"Missing frequency for indicator: {indicator.indicator_id}")
        
        # Check for valid values
        valid_units = {'USD', '%', 'ratio', 'score', 'count'}
        valid_directions = {'higher_is_better', 'lower_is_better', 'range'}
        valid_frequencies = {'daily', 'quarterly', 'annual'}
        valid_source_apis = {
            'quote', 'profile', 'key-metrics-ttm', 'ratios-ttm',
            'financial-growth', 'historical-price', 'dividends', 'technicals'
        }
        
        for indicator in indicators:
            if indicator.unit not in valid_units:
                errors.append(f"Invalid unit '{indicator.unit}' for indicator: {indicator.indicator_id}")
            
            if indicator.direction not in valid_directions:
                errors.append(f"Invalid direction '{indicator.direction}' for indicator: {indicator.indicator_id}")
            
            if indicator.frequency not in valid_frequencies:
                errors.append(f"Invalid frequency '{indicator.frequency}' for indicator: {indicator.indicator_id}")
            
            if indicator.source_api not in valid_source_apis:
                errors.append(f"Invalid source_api '{indicator.source_api}' for indicator: {indicator.indicator_id}")
        
        return errors
