"""
Base extractor class for system data extraction
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for all data extractors"""
    
    def __init__(self):
        """Initialize the extractor"""
        logger.debug(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        """
        Extract data from the system
        
        Returns:
            Dictionary containing extracted data
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate extracted data
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return isinstance(data, dict)
    
    def safe_extract(self) -> Dict[str, Any]:
        """
        Safely extract data with error handling
        
        Returns:
            Dictionary containing extracted data or empty dict on error
        """
        try:
            data = self.extract()
            if self.validate_data(data):
                return data
            else:
                logger.warning(f"{self.__class__.__name__} returned invalid data format")
                return {}
        except Exception as e:
            logger.error(f"Failed to extract data from {self.__class__.__name__}: {str(e)}")
            return {}