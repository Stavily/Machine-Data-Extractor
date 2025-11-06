"""
Disk information extractor
"""

import os
import subprocess
import platform
from typing import Dict, Any, List
import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class DiskExtractor(BaseExtractor):
    """Extracts disk information"""
    
    def extract(self) -> Dict[str, Any]:
        """Extract disk information"""
        try:
            disk_info = {
                'partitions': []
            }

            # Disk partitions using df command
            try:
                result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        headers = lines[0].split()
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 6:
                                disk_info['partitions'].append({
                                    'filesystem': parts[0],
                                    'size': parts[1],
                                    'used': parts[2],
                                    'available': parts[3],
                                    'use_percent': parts[4],
                                    'mountpoint': parts[5]
                                })
            except Exception as e:
                logger.warning(f"Failed to run df command: {str(e)}")

            # Disk usage for root filesystem
            try:
                statvfs = os.statvfs('/')
                disk_info['root_usage'] = {
                    'total': statvfs.f_blocks * statvfs.f_frsize,
                    'free': statvfs.f_available * statvfs.f_frsize,
                    'used': (statvfs.f_blocks - statvfs.f_available) * statvfs.f_frsize
                }
                if disk_info['root_usage']['total'] > 0:
                    disk_info['root_usage']['percent'] = round(
                        (disk_info['root_usage']['used'] / disk_info['root_usage']['total']) * 100, 1
                    )
            except Exception as e:
                logger.warning(f"Failed to get root filesystem usage: {str(e)}")

            return disk_info
        except Exception as e:
            logger.error(f"Failed to extract disk info: {str(e)}")
            return {}