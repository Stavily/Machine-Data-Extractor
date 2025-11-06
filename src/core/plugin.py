"""
Core plugin functionality for machine data extraction
"""

import datetime
from typing import Dict, Any
import logging

from ..extractors import (
    SystemExtractor,
    CpuExtractor,
    MemoryExtractor,
    DiskExtractor,
    ProcessExtractor
)
from ..monitoring import SystemMonitor

logger = logging.getLogger(__name__)


class MachineDataExtractorPlugin:
    """Main plugin class for machine data extraction"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the machine data extractor plugin

        Args:
            config: Configuration dictionary from plugin.yaml
        """
        self.config = config
        
        # Initialize extractors
        self.extractors = {
            'system': SystemExtractor(),
            'cpu': CpuExtractor(),
            'memory': MemoryExtractor(),
            'disk': DiskExtractor(),
            'processes': ProcessExtractor()
        }
        
        # Initialize monitor if needed
        self.monitor = None
        if config.get('monitor_interval', 0) > 0:
            self.monitor = SystemMonitor(config)
        
        logger.info("Initialized Machine Data Extractor plugin")

    def extract_data(self) -> Dict[str, Any]:
        """
        Extract machine data based on configuration
        Only extracts attributes that are explicitly enabled in config

        Returns:
            Dictionary containing extracted machine data
        """
        data = {
            'timestamp': datetime.datetime.now().isoformat()
        }

        # Always include system info
        data['system'] = self.extractors['system'].safe_extract()

        # Only extract if explicitly enabled
        if self.config.get('extract_cpu', False):
            data['cpu'] = self.extractors['cpu'].safe_extract()

        if self.config.get('extract_memory', False):
            data['memory'] = self.extractors['memory'].safe_extract()

        if self.config.get('extract_disk', False):
            data['disk'] = self.extractors['disk'].safe_extract()

        if self.config.get('extract_processes', False):
            data['processes'] = self.extractors['processes'].safe_extract()

        return data

    def extract_data_for_monitoring(self) -> Dict[str, Any]:
        """
        Extract machine data needed for monitoring/triggering
        Always includes CPU and memory data for trigger checks

        Returns:
            Dictionary containing extracted machine data for monitoring
        """
        data = {
            'timestamp': datetime.datetime.now().isoformat()
        }

        # Always include system info
        data['system'] = self.extractors['system'].safe_extract()

        # Always include CPU and memory for trigger checks
        data['cpu'] = self.extractors['cpu'].safe_extract()
        data['memory'] = self.extractors['memory'].safe_extract()

        # Include other data if explicitly enabled
        if self.config.get('extract_disk', False):
            data['disk'] = self.extractors['disk'].safe_extract()

        if self.config.get('extract_processes', False):
            data['processes'] = self.extractors['processes'].safe_extract()

        return data

    def start_monitoring(self) -> None:
        """
        Start monitoring loop if configured
        """
        if self.monitor:
            self.monitor.start_monitoring(self.extract_data_for_monitoring)
        else:
            logger.warning("Monitoring not configured or disabled")