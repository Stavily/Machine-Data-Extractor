"""
Tests for data extractors
"""

import unittest
from unittest.mock import patch, mock_open
import platform

from src.extractors import (
    SystemExtractor,
    CpuExtractor,
    MemoryExtractor,
    DiskExtractor,
    ProcessExtractor
)


class TestSystemExtractor(unittest.TestCase):
    """Test system information extractor"""

    def setUp(self):
        self.extractor = SystemExtractor()

    @patch('platform.system')
    @patch('platform.platform')
    @patch('platform.release')
    @patch('platform.version')
    @patch('platform.machine')
    @patch('platform.processor')
    @patch('socket.gethostname')
    def test_extract_system_info(self, mock_hostname, mock_processor, mock_machine,
                               mock_version, mock_release, mock_platform, mock_system):
        # Setup mocks
        mock_system.return_value = 'Linux'
        mock_platform.return_value = 'Linux-5.10.0-26-amd64-x86_64'
        mock_release.return_value = '5.10.0-26-amd64'
        mock_version.return_value = '#1 SMP Debian 5.10.197-1 (2023-09-29)'
        mock_machine.return_value = 'x86_64'
        mock_processor.return_value = ''
        mock_hostname.return_value = 'test-host'

        result = self.extractor.extract()

        self.assertIn('hostname', result)
        self.assertIn('platform', result)
        self.assertIn('system', result)
        self.assertEqual(result['hostname'], 'test-host')
        self.assertEqual(result['system'], 'Linux')


class TestCpuExtractor(unittest.TestCase):
    """Test CPU information extractor"""

    def setUp(self):
        self.extractor = CpuExtractor()

    @patch('os.cpu_count')
    @patch('platform.system')
    @patch('builtins.open', new_callable=mock_open, read_data='processor\t: 0\nprocessor\t: 1\n')
    @patch('subprocess.run')
    def test_extract_cpu_info(self, mock_subprocess, mock_file, mock_system, mock_cpu_count):
        mock_cpu_count.return_value = 2
        mock_system.return_value = 'Linux'

        # Mock subprocess for top command
        mock_result = unittest.mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '%Cpu(s):  5.0 us,  2.0 sy,  0.0 ni, 93.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st\n'
        mock_subprocess.return_value = mock_result

        result = self.extractor.extract()

        self.assertIn('cpu_count', result)
        self.assertIn('cpu_percent', result)
        self.assertEqual(result['cpu_count'], 2)


class TestMemoryExtractor(unittest.TestCase):
    """Test memory information extractor"""

    def setUp(self):
        self.extractor = MemoryExtractor()

    @patch('platform.system')
    @patch('builtins.open', new_callable=mock_open, read_data='MemTotal:        8192000 kB\nMemFree:         2048000 kB\n')
    def test_extract_memory_info(self, mock_file, mock_system):
        mock_system.return_value = 'Linux'

        result = self.extractor.extract()

        self.assertIn('virtual_memory', result)
        self.assertIn('total', result['virtual_memory'])
        self.assertIn('free', result['virtual_memory'])


class TestDiskExtractor(unittest.TestCase):
    """Test disk information extractor"""

    def setUp(self):
        self.extractor = DiskExtractor()

    @patch('subprocess.run')
    @patch('os.statvfs')
    def test_extract_disk_info(self, mock_statvfs, mock_subprocess):
        # Mock df command
        mock_result = unittest.mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Filesystem     1K-blocks    Used Available Use% Mounted on\n/dev/sda1       10000000 5000000  5000000  50% /\n'
        mock_subprocess.return_value = mock_result

        # Mock statvfs
        mock_stat = unittest.mock.MagicMock()
        mock_stat.f_blocks = 1000000
        mock_stat.f_frsize = 1024
        mock_stat.f_available = 500000
        mock_statvfs.return_value = mock_stat

        result = self.extractor.extract()

        self.assertIn('partitions', result)
        self.assertIn('root_usage', result)
        self.assertGreater(len(result['partitions']), 0)


class TestProcessExtractor(unittest.TestCase):
    """Test process information extractor"""

    def setUp(self):
        self.extractor = ProcessExtractor()

    @patch('subprocess.run')
    def test_extract_process_info(self, mock_subprocess):
        # Mock ps command output
        mock_result = unittest.mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1  12345  1234 ?        Ss   10:00   0:01 init\n'
        mock_subprocess.return_value = mock_result

        result = self.extractor.extract()

        self.assertIn('process_count', result)
        self.assertIn('processes', result)
        self.assertGreater(result['process_count'], 0)


if __name__ == '__main__':
    unittest.main()