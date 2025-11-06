"""
System information extractor
"""

import platform
import socket
import datetime
from typing import Dict, Any
import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class SystemExtractor(BaseExtractor):
    """Extracts general system information"""
    
    def extract(self) -> Dict[str, Any]:
        """Extract general system information"""
        try:
            system_info = {
                'hostname': socket.gethostname(),
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }

            # Get uptime from /proc/uptime on Linux
            try:
                if platform.system() == 'Linux':
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.read().split()[0])
                        system_info['uptime_seconds'] = int(uptime_seconds)
                        system_info['boot_time'] = (
                            datetime.datetime.now() - datetime.timedelta(seconds=uptime_seconds)
                        ).isoformat()
            except Exception:
                pass

            return system_info
        except Exception as e:
            logger.error(f"Failed to extract system info: {str(e)}")
            return {}