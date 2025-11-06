"""
Machine Data Extractor Plugin
Optimized modular structure for system monitoring and data extraction.
"""

__version__ = "1.0.0"
__author__ = "Stavily Team"
__description__ = "System monitoring and data extraction plugin"

from .core import MachineDataExtractorPlugin
from .extractors import *
from .monitoring import *
from .utils import *

__all__ = [
    'MachineDataExtractorPlugin',
    'SystemExtractor',
    'CpuExtractor',
    'MemoryExtractor',
    'DiskExtractor',
    'ProcessExtractor',
    'SystemMonitor',
    'validate_monitor_args',
    'validate_monitor_interval',
    'validate_config',
    'ValidationError',
    'format_success_output',
    'format_error_output',
    'format_trigger_event'
]