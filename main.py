#!/usr/bin/env python3
"""Machine Data Extractor Plugin - Main entry point"""

import argparse
import json
import logging
import sys
from typing import Dict, Any, List
import platform
import socket
import datetime
import os
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        logger.info("Initialized Machine Data Extractor plugin")

    def extract_cpu_info(self) -> Dict[str, Any]:
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
                                parts = line.split()
                                cpu_info['cpu_percent'] = float(parts[1].rstrip(',')) if len(parts) > 1 else None
                                break
            except Exception:
                pass

            return cpu_info
        except Exception as e:
            logger.error(f"Failed to extract CPU info: {str(e)}")
            return {}

    def extract_memory_info(self) -> Dict[str, Any]:
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

    def extract_disk_info(self) -> Dict[str, Any]:
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

    def extract_process_info(self) -> Dict[str, Any]:
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

    def extract_system_info(self) -> Dict[str, Any]:
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
        data['system'] = self.extract_system_info()

        # Only extract if explicitly enabled
        if self.config.get('extract_cpu', False):
            data['cpu'] = self.extract_cpu_info()

        if self.config.get('extract_memory', False):
            data['memory'] = self.extract_memory_info()

        if self.config.get('extract_disk', False):
            data['disk'] = self.extract_disk_info()

        if self.config.get('extract_processes', False):
            data['processes'] = self.extract_process_info()

        return data


def main():
    """Main entry point for the plugin"""
    try:
        parser = argparse.ArgumentParser(description='Machine Data Extractor Plugin')
        # Config args - only extract if explicitly enabled
        parser.add_argument('--extract-cpu', action='store_true', default=False, help='Extract CPU information')
        parser.add_argument('--extract-memory', action='store_true', default=False, help='Extract memory information')
        parser.add_argument('--extract-disk', action='store_true', default=False, help='Extract disk information')
        parser.add_argument('--extract-processes', action='store_true', default=False, help='Extract process information')

        args = parser.parse_args()

        config = {
            'extract_cpu': args.extract_cpu,
            'extract_memory': args.extract_memory,
            'extract_disk': args.extract_disk,
            'extract_processes': args.extract_processes
        }

        # Initialize plugin
        plugin = MachineDataExtractorPlugin(config)

        # Extract data
        result = plugin.extract_data()

        # Output result
        output = {
            'status': 'success',
            'data': result
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    except Exception as e:
        logger.error(f"Plugin execution failed: {str(e)}")
        result = {
            'status': 'error',
            'message': f'Plugin execution failed: {str(e)}'
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == '__main__':
    main()