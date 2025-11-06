"""
Tests for monitoring functionality
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from src.monitoring import SystemMonitor
from src.utils import format_trigger_event


class TestSystemMonitor(unittest.TestCase):
    """Test system monitoring functionality"""

    def setUp(self):
        self.config = {
            'monitor_interval': 30,
            'cpu_trigger_percentage': 80,
            'mem_trigger_percentage': 85
        }
        self.monitor = SystemMonitor(self.config)

    def test_initialization(self):
        """Test monitor initialization"""
        self.assertEqual(self.monitor.monitor_interval, 30)
        self.assertEqual(self.monitor.cpu_trigger, 80)
        self.assertEqual(self.monitor.mem_trigger, 85)

    def test_should_trigger_cpu(self):
        """Test CPU trigger detection"""
        data = {
            'cpu': {'cpu_percent': 85.0},
            'memory': {'virtual_memory': {'percent': 50.0}}
        }
        self.assertTrue(self.monitor.should_trigger(data))

    def test_should_trigger_memory(self):
        """Test memory trigger detection"""
        data = {
            'cpu': {'cpu_percent': 50.0},
            'memory': {'virtual_memory': {'percent': 90.0}}
        }
        self.assertTrue(self.monitor.should_trigger(data))

    def test_should_not_trigger(self):
        """Test no trigger when thresholds not exceeded"""
        data = {
            'cpu': {'cpu_percent': 50.0},
            'memory': {'virtual_memory': {'percent': 60.0}}
        }
        self.assertFalse(self.monitor.should_trigger(data))

    def test_should_not_trigger_zero_limits(self):
        """Test no trigger when limits are zero"""
        config = {
            'monitor_interval': 30,
            'cpu_trigger_percentage': 0,
            'mem_trigger_percentage': 0
        }
        monitor = SystemMonitor(config)
        data = {
            'cpu': {'cpu_percent': 90.0},
            'memory': {'virtual_memory': {'percent': 95.0}}
        }
        self.assertFalse(monitor.should_trigger(data))

    def test_output_trigger_event(self):
        """Test trigger event output formatting"""
        data = {
            'timestamp': '2025-01-01T12:00:00',
            'cpu': {'cpu_percent': 85.0}
        }

        with patch('src.monitoring.monitor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.isoformat.return_value = '2025-01-01T12:05:00'
            result = self.monitor.output_trigger_event(data)

        self.assertIn('data', result)
        self.assertIn('date_triggered', result)
        self.assertEqual(result['data'], data)

    @patch('time.sleep')
    @patch('src.monitoring.monitor.SystemMonitor.should_trigger')
    def test_monitoring_loop(self, mock_should_trigger, mock_sleep):
        """Test monitoring loop execution"""
        mock_should_trigger.return_value = False

        # Mock data extractor
        def mock_extractor():
            return {'timestamp': '2025-01-01T12:00:00'}

        # Test with KeyboardInterrupt to stop loop
        with patch('builtins.print') as mock_print:
            # Simulate KeyboardInterrupt after first iteration
            mock_sleep.side_effect = KeyboardInterrupt()
            self.monitor.start_monitoring(mock_extractor)

        # Verify sleep was called
        mock_sleep.assert_called_once_with(30)


class TestFormatting(unittest.TestCase):
    """Test output formatting utilities"""

    def test_format_trigger_event(self):
        """Test trigger event formatting"""
        data = {'test': 'data'}

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = '2025-01-01T12:00:00'
            result = format_trigger_event(data)

        parsed = json.loads(result)
        self.assertIn('data', parsed)
        self.assertIn('date_triggered', parsed)
        self.assertEqual(parsed['data'], data)


if __name__ == '__main__':
    unittest.main()