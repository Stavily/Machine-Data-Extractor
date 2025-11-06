"""
Process information extractor
"""

import subprocess
import platform
from typing import Dict, Any, List
import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class ProcessExtractor(BaseExtractor):
    """Extracts process information"""
    
    def extract(self) -> Dict[str, Any]:
        """Extract process information"""
        try:
            processes = []

            # Use ps command to get process information
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        # Skip header
                        for line in lines[1:]:
                            parts = line.split(None, 10)  # Split on whitespace, max 11 parts
                            if len(parts) >= 11:
                                try:
                                    processes.append({
                                        'user': parts[0],
                                        'pid': int(parts[1]),
                                        'cpu_percent': float(parts[2]),
                                        'memory_percent': float(parts[3]),
                                        'vsz': parts[4],  # Virtual memory size
                                        'rss': parts[5],  # Resident set size
                                        'tty': parts[6],
                                        'stat': parts[7],
                                        'start': parts[8],
                                        'time': parts[9],
                                        'command': parts[10]
                                    })
                                except (ValueError, IndexError):
                                    continue

                        # Sort by CPU usage descending
                        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            except Exception as e:
                logger.warning(f"Failed to run ps command: {str(e)}")

            return {
                'process_count': len(processes),
                'processes': processes[:50]  # Limit to top 50 processes
            }
        except Exception as e:
            logger.error(f"Failed to extract process info: {str(e)}")
            return {}