"""
Memory information extractor
"""

import platform
from typing import Dict, Any
import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class MemoryExtractor(BaseExtractor):
    """Extracts memory information"""
    
    def extract(self) -> Dict[str, Any]:
        """Extract memory information"""
        try:
            memory_info = {}

            # Memory info from /proc/meminfo on Linux
            if platform.system() == 'Linux':
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = {}
                        for line in f:
                            parts = line.split()
                            if len(parts) >= 2:
                                key = parts[0].rstrip(':')
                                value = int(parts[1]) * 1024  # Convert to bytes
                                meminfo[key] = value

                    memory_info['virtual_memory'] = {
                        'total': meminfo.get('MemTotal'),
                        'free': meminfo.get('MemFree'),
                        'available': meminfo.get('MemAvailable'),
                        'buffers': meminfo.get('Buffers', 0),
                        'cached': meminfo.get('Cached', 0),
                        'swap_cached': meminfo.get('SwapCached', 0),
                        'active': meminfo.get('Active', 0),
                        'inactive': meminfo.get('Inactive', 0)
                    }

                    # Calculate used and percent
                    if memory_info['virtual_memory']['total']:
                        total = memory_info['virtual_memory']['total']
                        free = memory_info['virtual_memory'].get('free', 0)
                        used = total - free
                        memory_info['virtual_memory']['used'] = used
                        memory_info['virtual_memory']['percent'] = round((used / total) * 100, 1)

                    # Swap memory
                    memory_info['swap_memory'] = {
                        'total': meminfo.get('SwapTotal'),
                        'free': meminfo.get('SwapFree')
                    }
                    if memory_info['swap_memory']['total']:
                        total = memory_info['swap_memory']['total']
                        free = memory_info['swap_memory'].get('free', 0)
                        used = total - free
                        memory_info['swap_memory']['used'] = used
                        memory_info['swap_memory']['percent'] = round((used / total) * 100, 1) if total > 0 else 0

                except Exception as e:
                    logger.warning(f"Failed to read /proc/meminfo: {str(e)}")

            return memory_info
        except Exception as e:
            logger.error(f"Failed to extract memory info: {str(e)}")
            return {}