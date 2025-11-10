#!/usr/bin/env python3
"""
Stavily Agent Client - Shared module for plugin communication with Stavily agents.

This module provides a unified interface for plugins to communicate with Stavily agents
using JSON-RPC 2.0 over Unix Domain Sockets. It handles connection management, error
handling, and provides high-level methods for common agent interactions.

Features:
- JSON-RPC 2.0 communication over Unix sockets
- Automatic connection management and retries
- Structured logging and error handling
- High-level methods for common operations
- Thread-safe operations
- Comprehensive error handling with custom exceptions

Usage:
    from stavily_agent_client import StavilyAgentClient

    client = StavilyAgentClient()
    client.connect()

    # Report a trigger event
    client.report_trigger("cpu_high", {"usage": 85})

    # Upload logs
    client.upload_logs([{"level": "INFO", "message": "Plugin started"}])

    # Get agent information
    info = client.get_agent_info()

    # Get configuration
    config = client.get_config("plugin_section")
"""

import os
import socket
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)


class StavilyAgentError(Exception):
    """Base exception for Stavily agent communication errors."""
    pass


class ConnectionError(StavilyAgentError):
    """Raised when connection to agent fails."""
    pass


class RPCError(StavilyAgentError):
    """Raised when RPC call fails."""

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        super().__init__(f"RPC Error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class TimeoutError(StavilyAgentError):
    """Raised when RPC call times out."""
    pass


@dataclass
class AgentInfo:
    """Agent information structure."""
    agent_id: str
    version: str
    environment: str


class StavilyAgentClient:
    """
    Client for communicating with Stavily agents via JSON-RPC over Unix sockets.

    This class provides a high-level interface for plugins to interact with
    Stavily agents, handling all the low-level socket communication and
    JSON-RPC protocol details.
    """

    def __init__(self,
                 socket_path: Optional[str] = None,
                 timeout: float = 5.0,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the agent client.

        Args:
            socket_path: Path to the agent socket. If None, uses STAVILY_AGENT_SOCKET env var.
            timeout: Socket timeout in seconds.
            max_retries: Maximum number of connection retries.
            retry_delay: Delay between retries in seconds.
        """
        self.socket_path = socket_path or os.environ.get('STAVILY_AGENT_SOCKET')
        if not self.socket_path:
            raise ValueError("Socket path not provided and STAVILY_AGENT_SOCKET not set")

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._request_id = 0
        self._connected = False

        logger.debug(f"Initialized StavilyAgentClient with socket: {self.socket_path}")

    def connect(self) -> None:
        """
        Establish connection to the agent.

        Raises:
            ConnectionError: If connection fails after all retries.
        """
        if self._connected:
            return

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Test connection with a ping
                self._call("ping", {})
                self._connected = True
                logger.info("Successfully connected to Stavily agent")
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All connection attempts failed: {e}")

        raise ConnectionError(f"Failed to connect to agent after {self.max_retries + 1} attempts: {last_error}")

    def disconnect(self) -> None:
        """Disconnect from the agent."""
        self._connected = False
        logger.debug("Disconnected from Stavily agent")

    def is_connected(self) -> bool:
        """Check if client is connected to agent."""
        return self._connected

    def report_trigger(self, trigger_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report a trigger event to the agent.

        Args:
            trigger_name: Name of the trigger (e.g., "cpu_high", "memory_low").
            payload: Additional data about the trigger event.

        Returns:
            Acknowledgment response from agent.

        Raises:
            RPCError: If the RPC call fails.
            ConnectionError: If not connected to agent.
        """
        if not self._connected:
            raise ConnectionError("Not connected to agent")

        params = {
            "trigger_name": trigger_name,
            "payload": payload
        }

        result = self._call("report_trigger", params)
        logger.debug(f"Reported trigger '{trigger_name}' to agent")
        return result

    def upload_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload structured logs to the agent.

        Args:
            logs: List of log entries with 'level', 'message', and 'timestamp' fields.

        Returns:
            Upload acknowledgment from agent.

        Raises:
            RPCError: If the RPC call fails.
            ConnectionError: If not connected to agent.
        """
        if not self._connected:
            raise ConnectionError("Not connected to agent")

        # Validate log format
        for log_entry in logs:
            if not all(key in log_entry for key in ['level', 'message', 'timestamp']):
                raise ValueError("Log entries must contain 'level', 'message', and 'timestamp' fields")

        params = {"logs": logs}
        result = self._call("upload_logs", params)

        log_count = len(logs)
        logger.debug(f"Uploaded {log_count} log entries to agent")
        return result

    def get_agent_info(self) -> AgentInfo:
        """
        Get information about the connected agent.

        Returns:
            AgentInfo object with agent details.

        Raises:
            RPCError: If the RPC call fails.
            ConnectionError: If not connected to agent.
        """
        if not self._connected:
            raise ConnectionError("Not connected to agent")

        result = self._call("get_agent_info")
        return AgentInfo(
            agent_id=result.get("agent_id", "unknown"),
            version=result.get("version", "unknown"),
            environment=result.get("environment", "unknown")
        )

    def get_config(self, section: str) -> Dict[str, Any]:
        """
        Get configuration section from the agent.

        Args:
            section: Configuration section name.

        Returns:
            Configuration data for the requested section.

        Raises:
            RPCError: If the RPC call fails.
            ConnectionError: If not connected to agent.
        """
        if not self._connected:
            raise ConnectionError("Not connected to agent")

        params = {"section": section}
        result = self._call("get_config", params)
        return result.get("config", {})

    def _get_next_request_id(self) -> int:
        """Get next unique request ID."""
        self._request_id += 1
        return self._request_id

    def _call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make a JSON-RPC call to the agent.

        Args:
            method: RPC method name.
            params: Method parameters.

        Returns:
            RPC result.

        Raises:
            RPCError: If the RPC call returns an error.
            ConnectionError: If socket communication fails.
            TimeoutError: If the call times out.
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._get_next_request_id()
        }

        if params:
            request["params"] = params

        request_json = json.dumps(request)

        try:
            # Create socket connection
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            try:
                sock.connect(self.socket_path)

                # Send request
                sock.sendall((request_json + "\n").encode())

                # Read response
                response_data = sock.recv(65536).decode().strip()

                if not response_data:
                    raise ConnectionError("Empty response from agent")

                response = json.loads(response_data)

                # Check for RPC error
                if "error" in response:
                    error = response["error"]
                    raise RPCError(error["code"], error["message"], error.get("data"))

                # Return result
                return response.get("result")

            finally:
                sock.close()

        except socket.timeout:
            raise TimeoutError(f"RPC call to '{method}' timed out after {self.timeout}s")
        except socket.error as e:
            raise ConnectionError(f"Socket error during RPC call to '{method}': {e}")
        except json.JSONDecodeError as e:
            raise StavilyAgentError(f"Invalid JSON response from agent: {e}")

    @contextmanager
    def session(self):
        """
        Context manager for agent client sessions.

        Automatically connects on enter and disconnects on exit.
        """
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()


# Convenience functions for quick operations
def quick_report_trigger(trigger_name: str, payload: Dict[str, Any],
                        socket_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick function to report a trigger without explicit client management.

    Args:
        trigger_name: Name of the trigger.
        payload: Trigger payload.
        socket_path: Optional socket path override.

    Returns:
        Acknowledgment response.
    """
    with StavilyAgentClient(socket_path).session() as client:
        return client.report_trigger(trigger_name, payload)


def quick_upload_logs(logs: List[Dict[str, Any]],
                     socket_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick function to upload logs without explicit client management.

    Args:
        logs: List of log entries.
        socket_path: Optional socket path override.

    Returns:
        Upload acknowledgment.
    """
    with StavilyAgentClient(socket_path).session() as client:
        return client.upload_logs(logs)


def quick_get_agent_info(socket_path: Optional[str] = None) -> AgentInfo:
    """
    Quick function to get agent info without explicit client management.

    Args:
        socket_path: Optional socket path override.

    Returns:
        Agent information.
    """
    with StavilyAgentClient(socket_path).session() as client:
        return client.get_agent_info()


def quick_get_config(section: str, socket_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick function to get config without explicit client management.

    Args:
        section: Configuration section name.
        socket_path: Optional socket path override.

    Returns:
        Configuration data.
    """
    with StavilyAgentClient(socket_path).session() as client:
        return client.get_config(section)


# Export public API
__all__ = [
    "StavilyAgentClient",
    "StavilyAgentError",
    "ConnectionError",
    "RPCError",
    "TimeoutError",
    "AgentInfo",
    "quick_report_trigger",
    "quick_upload_logs",
    "quick_get_agent_info",
    "quick_get_config"
]