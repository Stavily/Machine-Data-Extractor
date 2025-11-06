"""
Output formatting utilities
"""

import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def format_success_output(data: Dict[str, Any]) -> str:
    """
    Format successful extraction output
    
    Args:
        data: Extracted data
        
    Returns:
        JSON formatted string
    """
    output = {
        'status': 'success',
        'data': data
    }
    return json.dumps(output, indent=2)


def format_error_output(message: str) -> str:
    """
    Format error output
    
    Args:
        message: Error message
        
    Returns:
        JSON formatted string
    """
    output = {
        'status': 'error',
        'message': message
    }
    return json.dumps(output)


def format_trigger_event(data: Dict[str, Any]) -> str:
    """
    Format trigger event output
    
    Args:
        data: System data that triggered the event
        
    Returns:
        JSON formatted string
    """
    import datetime
    trigger_output = {
        'data': data,
        'date_triggered': datetime.datetime.now().isoformat()
    }
    return json.dumps(trigger_output, indent=2)