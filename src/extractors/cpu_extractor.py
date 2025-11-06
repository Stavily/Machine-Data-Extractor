"""
CPU information extractor
"""

import os
import platform
import subprocess
import re
from typing import Dict, Any
import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class CpuExtractor(BaseExtractor):
    """Extracts CPU information"""
    
    def extract(self) -> Dict[str, Any]:
        """Extract CPU information"""
        try:
            cpu_info = {}

            # CPU count using os
            try:
                cpu_info['cpu_count'] = os.cpu_count()
            except Exception:
                cpu_info['cpu_count'] = None

            # Try to get CPU info from /proc/cpuinfo on Linux
            try:
                if platform.system() == 'Linux':
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                    cpu_count = cpuinfo.count('processor\t:')
                    if cpu_count > 0:
                        cpu_info['cpu_count'] = cpu_count
            except Exception:
                pass

            # CPU usage using top or similar
            try:
                if platform.system() == 'Linux':
                    result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if '%Cpu(s):' in line:
                                # Parse CPU usage from top output
                                # Format: %Cpu(s):  9.8 us,  8.7 sy,  0.0 ni, 81.5 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
                                # We want the total idle percentage, then calculate used as 100 - idle
                                # Use regex to find the idle percentage more reliably
                                match = re.search(r'(\d+\.\d+)\s+id', line)
                                if match:
                                    try:
                                        idle_percent = float(match.group(1))
                                        cpu_info['cpu_percent'] = round(100.0 - idle_percent, 1)
                                    except (ValueError, IndexError):
                                        cpu_info['cpu_percent'] = None
                                else:
                                    # Fallback to old parsing if regex fails
                                    parts = line.split()
                                    if len(parts) >= 8:  # Make sure we have enough parts
                                        try:
                                            idle_percent = float(parts[7].rstrip(','))  # The 'id' (idle) percentage
                                            cpu_info['cpu_percent'] = round(100.0 - idle_percent, 1)
                                        except (ValueError, IndexError):
                                            cpu_info['cpu_percent'] = None
                                break
            except Exception:
                pass

            return cpu_info
        except Exception as e:
            logger.error(f"Failed to extract CPU info: {str(e)}")
            return {}