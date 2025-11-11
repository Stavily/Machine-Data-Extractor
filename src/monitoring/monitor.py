"""
System monitoring functionality
"""

import time
import datetime
from typing import Dict, Any, Callable
import logging
import sys
import os

# Import shared agent client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from stavily_agent_client import StavilyAgentClient, StavilyAgentError

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Handles system monitoring with threshold-based triggers"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the system monitor

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.monitor_interval = config.get('monitor_interval', 30)
        self.cpu_trigger = config.get('cpu_trigger_percentage', 0)
        self.mem_trigger = config.get('mem_trigger_percentage', 0)

        # Initialize agent client
        self.agent_client = None
        try:
            self.agent_client = StavilyAgentClient()
            self.agent_client.connect()
            logger.info("Connected to Stavily agent")
        except StavilyAgentError as e:
            raise f"Failed to connect to agent: {e}"
        except Exception as e:
            raise f"Unexpected error connecting to agent: {e}"

        logger.debug(f"Initialized SystemMonitor with interval={self.monitor_interval}s, "
                    f"CPU trigger={self.cpu_trigger}%, Memory trigger={self.mem_trigger}%")
    
    def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if CPU or memory usage exceeds trigger thresholds

        Args:
            data: System data to check

        Returns:
            True if trigger conditions are met
        """
        triggered = False

        # Debug: Log current data extraction
        logger.debug(f"Checking triggers with data timestamp: {data.get('timestamp', 'unknown')}")

        # Check CPU trigger
        if self.cpu_trigger > 0:
            if 'cpu' in data and 'cpu_percent' in data['cpu']:
                cpu_percent = data['cpu']['cpu_percent']
                if cpu_percent is not None and isinstance(cpu_percent, (int, float)) and cpu_percent > self.cpu_trigger:
                    logger.info(f"CPU trigger activated: {cpu_percent}% > {self.cpu_trigger}%")

                    # Report trigger to agent
                    if self.agent_client and self.agent_client.is_connected():
                        try:
                            self.agent_client.report_trigger("cpu_high", {
                                "usage": cpu_percent,
                                "threshold": self.cpu_trigger,
                                "timestamp": data.get('timestamp', datetime.datetime.now().isoformat())
                            })
                        except StavilyAgentError as e:
                            logger.warning(f"Failed to report CPU trigger to agent: {e}")

                    triggered = True
            else:
                logger.warning("CPU data not available for trigger check - this should not happen in monitoring mode")
                logger.debug(f"Available data keys: {list(data.keys())}")
                if 'cpu' in data:
                    logger.debug(f"CPU data content: {data['cpu']}")
        else:
            logger.debug("CPU trigger disabled (threshold = 0)")

        # Check memory trigger
        if self.mem_trigger > 0:
            if 'memory' in data and 'virtual_memory' in data['memory'] and 'percent' in data['memory']['virtual_memory']:
                mem_percent = data['memory']['virtual_memory']['percent']
                if mem_percent is not None and mem_percent > self.mem_trigger:
                    logger.info(f"Memory trigger activated: {mem_percent}% > {self.mem_trigger}%")

                    # Report trigger to agent
                    if self.agent_client and self.agent_client.is_connected():
                        try:
                            self.agent_client.report_trigger("memory_high", {
                                "usage": mem_percent,
                                "threshold": self.mem_trigger,
                                "timestamp": data.get('timestamp', datetime.datetime.now().isoformat())
                            })
                        except StavilyAgentError as e:
                            logger.warning(f"Failed to report memory trigger to agent: {e}")

                    triggered = True
            else:
                logger.debug("Memory data not available for trigger check")
        else:
            logger.debug("Memory trigger disabled (threshold = 0)")

        logger.debug(f"Trigger check result: {'TRIGGERED' if triggered else 'no trigger'}")
        return triggered
    
    def output_trigger_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Output trigger event in structured format
        
        Args:
            data: System data that triggered the event
            
        Returns:
            Trigger event dictionary
        """
        trigger_output = {
            'data': data,
            'date_triggered': datetime.datetime.now().isoformat()
        }
        return trigger_output
    
    def start_monitoring(self, data_extractor: Callable[[], Dict[str, Any]],
                        trigger_callback: Callable[[Dict[str, Any]], None] = None) -> None:
        """
        Start the monitoring loop

        Args:
            data_extractor: Function to extract system data
            trigger_callback: Optional callback for trigger events
        """
        logger.info(f"Starting monitoring loop with {self.monitor_interval}s interval")
        logger.info(f"Monitor configuration: CPU trigger={self.cpu_trigger}%, Memory trigger={self.mem_trigger}%")

        # Log monitoring start to agent
        if self.agent_client and self.agent_client.is_connected():
            try:
                self.agent_client.upload_logs([{
                    "level": "INFO",
                    "message": f"Machine Data Extractor monitoring started with CPU trigger={self.cpu_trigger}%, Memory trigger={self.mem_trigger}%",
                    "timestamp": datetime.datetime.now().isoformat()
                }])
            except StavilyAgentError as e:
                logger.warning(f"Failed to log monitoring start to agent: {e}")

        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                # Extract current data
                data = data_extractor()

                # Upload periodic monitoring data to agent
                if self.agent_client and self.agent_client.is_connected():
                    try:
                        cpu_usage = data.get('cpu', {}).get('cpu_percent', 'unknown')
                        mem_usage = data.get('memory', {}).get('virtual_memory', {}).get('percent', 'unknown')
                        self.agent_client.upload_logs([{
                            "level": "INFO",
                            "message": f"Monitoring cycle #{cycle_count}: CPU={cpu_usage}%, Memory={mem_usage}%",
                            "timestamp": data.get('timestamp', datetime.datetime.now().isoformat())
                        }])
                    except StavilyAgentError as e:
                        logger.warning(f"Failed to upload monitoring data to agent: {e}")

                # Check if we should trigger
                trigger_result = self.should_trigger(data)
                if trigger_result:
                    logger.info(f"Trigger conditions met in cycle #{cycle_count}")
                    trigger_event = self.output_trigger_event(data)
                    if trigger_callback:
                        trigger_callback(trigger_event)
                    else:
                        # Default behavior: print JSON
                        import json
                        encloser = "-" * 10 + " TRIGGER EVENT "+ "-" * 10
                        print(encloser)
                        print(json.dumps(trigger_event, indent=2))
                        print(encloser)

                # Wait for next cycle
                time.sleep(self.monitor_interval)

        except KeyboardInterrupt:
            logger.info(f"Monitoring stopped by user after {cycle_count} cycles")

            # Log monitoring stop to agent
            if self.agent_client and self.agent_client.is_connected():
                try:
                    self.agent_client.upload_logs([{
                        "level": "INFO",
                        "message": f"Machine Data Extractor monitoring stopped after {cycle_count} cycles",
                        "timestamp": datetime.datetime.now().isoformat()
                    }])
                except StavilyAgentError as e:
                    logger.warning(f"Failed to log monitoring stop to agent: {e}")

        except Exception as e:
            logger.error(f"Monitoring loop error after {cycle_count} cycles: {str(e)}")

            # Log error to agent
            if self.agent_client and self.agent_client.is_connected():
                try:
                    self.agent_client.upload_logs([{
                        "level": "ERROR",
                        "message": f"Machine Data Extractor monitoring error after {cycle_count} cycles: {str(e)}",
                        "timestamp": datetime.datetime.now().isoformat()
                    }])
                except StavilyAgentError as e:
                    logger.warning(f"Failed to log monitoring error to agent: {e}")

            raise