#!/usr/bin/env python3
"""Machine Data Extractor Plugin - Main entry point"""

import argparse
import sys
import logging

from src.core import MachineDataExtractorPlugin
from src.utils import (
    validate_config,
    ValidationError,
    format_success_output,
    format_error_output
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the plugin"""
    try:
        parser = argparse.ArgumentParser(description='Machine Data Extractor Plugin')
        # CPU and memory are always extracted for monitoring

        # Monitor loop args
        parser.add_argument('--monitor-interval', type=int, default=30,
                          help='Monitor interval in seconds (default: 30, 0 = no monitoring)')
        parser.add_argument('--cpu-trigger-percentage', type=int, required=True,
                          help='CPU trigger percentage (0-100, 0 = no limit) - MANDATORY')
        parser.add_argument('--mem-trigger-percentage', type=int, required=True,
                          help='Memory trigger percentage (0-100, 0 = no limit) - MANDATORY')

        args = parser.parse_args()

        config = {
            'extract_cpu': True,  # Always extract CPU for monitoring
            'extract_memory': True,  # Always extract memory for monitoring
            'extract_disk': False,
            'extract_processes': False,
            'monitor_interval': args.monitor_interval,
            'cpu_trigger_percentage': args.cpu_trigger_percentage,
            'mem_trigger_percentage': args.mem_trigger_percentage
        }

        # Validate configuration
        validate_config(config)

        # Initialize plugin
        plugin = MachineDataExtractorPlugin(config)

        # If no monitoring, run single extraction
        if args.monitor_interval == 0:
            result = plugin.extract_data()
            print(format_success_output(result))
            sys.exit(0)

        # Start monitoring loop
        plugin.start_monitoring()

    except ValidationError as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        print(format_error_output(f'Configuration validation failed: {str(e)}'))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Plugin execution failed: {str(e)}")
        print(format_error_output(f'Plugin execution failed: {str(e)}'))
        sys.exit(1)


if __name__ == '__main__':
    main()