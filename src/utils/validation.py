"""
Validation utilities for configuration and data
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_monitor_args(cpu_trigger: int, mem_trigger: int) -> None:
    """
    Validate monitoring arguments
    
    Args:
        cpu_trigger: CPU trigger percentage
        mem_trigger: Memory trigger percentage
        
    Raises:
        ValidationError: If validation fails
    """
    if cpu_trigger < 0 or cpu_trigger > 100:
        raise ValidationError("CPU trigger percentage must be between 0 and 100")
    if mem_trigger < 0 or mem_trigger > 100:
        raise ValidationError("Memory trigger percentage must be between 0 and 100")


def validate_monitor_interval(interval: int) -> None:
    """
    Validate monitor interval
    
    Args:
        interval: Monitor interval in seconds
        
    Raises:
        ValidationError: If validation fails
    """
    if interval < 0:
        raise ValidationError("Monitor interval must be non-negative")


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate complete configuration
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    # Validate monitoring parameters
    cpu_trigger = config.get('cpu_trigger_percentage', 0)
    mem_trigger = config.get('mem_trigger_percentage', 0)
    monitor_interval = config.get('monitor_interval', 30)
    
    validate_monitor_args(cpu_trigger, mem_trigger)
    validate_monitor_interval(monitor_interval)
    
    logger.debug("Configuration validation passed")