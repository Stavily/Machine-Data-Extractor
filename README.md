# Machine Data Extractor Plugin

A Stavily plugin for extracting system information including CPU, memory, disk, and process data from the host machine. Can run in monitoring loop mode to trigger when CPU or memory thresholds are exceeded.

## Architecture

The plugin has been refactored into a modular architecture for better maintainability and testability:

```
Machine-Data-Extractor/
├── src/
│   ├── __init__.py              # Main package exports
│   ├── core/
│   │   ├── __init__.py          # Core functionality exports
│   │   └── plugin.py            # Main plugin class
│   ├── extractors/
│   │   ├── __init__.py          # Extractor exports
│   │   ├── base.py              # Abstract base extractor
│   │   ├── system_extractor.py  # System info extraction
│   │   ├── cpu_extractor.py     # CPU info extraction
│   │   ├── memory_extractor.py  # Memory info extraction
│   │   ├── disk_extractor.py    # Disk info extraction
│   │   └── process_extractor.py # Process info extraction
│   ├── monitoring/
│   │   ├── __init__.py          # Monitoring exports
│   │   └── monitor.py           # System monitoring logic
│   └── utils/
│       ├── __init__.py          # Utility exports
│       ├── validation.py        # Input validation
│       └── formatting.py        # Output formatting
├── tests/
│   ├── __init__.py
│   ├── test_extractors.py       # Extractor unit tests
│   └── test_monitoring.py       # Monitoring unit tests
├── main.py                      # Entry point
├── plugin.yaml                  # Plugin configuration
└── README.md                    # This file
```

## Features

- **System Information**: Basic system details (hostname, platform, uptime, etc.)
- **CPU Information**: CPU count and current usage percentage
- **Memory Information**: Detailed memory and swap statistics
- **Disk Information**: Filesystem partitions and usage data
- **Process Information**: Running processes with CPU/memory usage (top 50 by CPU)
- **Monitoring Loop**: Continuous monitoring with threshold-based triggers
- **JSON Output**: Structured output for system data or trigger events
- **Modular Design**: Clean separation of concerns with testable components
- **Error Handling**: Comprehensive error handling and validation

## Configuration

The plugin supports selective data extraction through configuration flags:

- `extract_disk`: Extract disk information
- `extract_processes`: Extract process information

CPU and memory information are always extracted for monitoring purposes. By default, disk and process extraction are disabled. Only enabled options will be included in the output.

## Monitoring Loop Features

The plugin can run in continuous monitoring mode with the following parameters:

- `monitor_interval`: Interval between checks in seconds (default: 30, 0 = no monitoring)
- `cpu_trigger_percentage`: CPU usage threshold for triggering (0-100, 0 = no limit) - **MANDATORY**
- `mem_trigger_percentage`: Memory usage threshold for triggering (0-100, 0 = no limit) - **MANDATORY**

## Usage

### Command Line

#### Single Extraction Mode (Original behavior)
```bash
# Extract CPU and memory information (always included)
python3 main.py --monitor-interval 0 --cpu-trigger-percentage 50 --mem-trigger-percentage 70

# Extract all available information
python3 main.py --extract-disk --extract-processes --monitor-interval 0 --cpu-trigger-percentage 50 --mem-trigger-percentage 70
```

#### Monitoring Loop Mode (New functionality)
```bash
# Monitor CPU and memory every 10 seconds
python3 main.py --monitor-interval 10 --cpu-trigger-percentage 80 --mem-trigger-percentage 85

# Monitor with different intervals and thresholds
python3 main.py --monitor-interval 5 --cpu-trigger-percentage 70 --mem-trigger-percentage 75

# Monitor with no limits (only displays system info)
python3 main.py --monitor-interval 30 --cpu-trigger-percentage 0 --mem-trigger-percentage 0

# Single extraction (disable monitoring loop)
python3 main.py --monitor-interval 0 --cpu-trigger-percentage 50 --mem-trigger-percentage 50
```

### Plugin Configuration

Configure the plugin in `plugin.yaml`:

```yaml
configuration:
  extract_disk: false    # Disable disk extraction
  extract_processes: false # Disable process extraction
  monitor_interval: 30   # Check every 30 seconds (0 = no monitoring)
  cpu_trigger_percentage: 80  # Trigger when CPU > 80%
  mem_trigger_percentage: 85  # Trigger when memory > 85%
```

## Output Format

### Single Extraction Output

When running in single extraction mode (monitor-interval = 0):

```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-10-14T23:25:43.243689",
    "system": {
      "hostname": "machine-name",
      "platform": "Linux-5.10.0-26-amd64-x86_64-with-glibc2.36",
      "system": "Linux",
      "release": "5.10.0-26-amd64",
      "version": "#1 SMP Debian 5.10.197-1 (2023-09-29)",
      "machine": "x86_64",
      "processor": "",
      "uptime_seconds": 120956,
      "boot_time": "2025-10-13T13:49:47.145334"
    },
    "cpu": {
      "cpu_count": 8,
      "cpu_percent": 31.2
    },
    "memory": {
      "virtual_memory": {
        "total": 49877946368,
        "free": 23271661568,
        "available": 35254079488,
        "used": 26606284800,
        "percent": 53.3,
        "buffers": 570273792,
        "cached": 12536913920,
        "active": 5838303232,
        "inactive": 17886846976
      },
      "swap_memory": {
        "total": 0,
        "free": 0
      }
    }
  }
}
```

### Trigger Event Output

When running in monitoring loop mode and a threshold is exceeded:

```json
{
  "data": {
    "timestamp": "2025-10-14T23:25:43.243689",
    "system": {
      "hostname": "machine-name",
      "platform": "Linux-5.10.0-26-amd64-x86_64-with-glibc2.36",
      "system": "Linux",
      "release": "5.10.0-26-amd64",
      "version": "#1 SMP Debian 5.10.197-1 (2023-09-29)",
      "machine": "x86_64",
      "processor": "",
      "uptime_seconds": 120956,
      "boot_time": "2025-10-13T13:49:47.145334"
    },
    "cpu": {
      "cpu_count": 8,
      "cpu_percent": 85.2
    },
    "memory": {
      "virtual_memory": {
        "total": 49877946368,
        "free": 23271661568,
        "available": 35254079488,
        "used": 26606284800,
        "percent": 53.3,
        "buffers": 570273792,
        "cached": 12536913920,
        "active": 5838303232,
        "inactive": 17886846976
      },
      "swap_memory": {
        "total": 0,
        "free": 0
      }
    }
  },
  "date_triggered": "2025-10-14T23:25:43.243689"
}
```

## Testing

The plugin includes comprehensive unit tests:

```bash
# Run all tests
python3 -m unittest discover tests/ -v

# Run specific test file
python3 -m unittest tests.test_extractors -v
python3 -m unittest tests.test_monitoring -v
```

## Requirements

- Python 3.8+
- Linux operating system (uses system commands and /proc filesystem)
- No external dependencies (uses only Python standard library)

## Installation

1. Place the plugin files in a directory
2. Ensure `main.py` is executable
3. Configure `plugin.yaml` as needed
4. Run the plugin using the Stavily framework

## Data Sources

- **System info**: Python `platform` and `socket` modules, `/proc/uptime`
- **CPU info**: `os.cpu_count()`, `/proc/cpuinfo`, `top` command
- **Memory info**: `/proc/meminfo`
- **Disk info**: `df -h` command, `os.statvfs()`
- **Process info**: `ps aux` command

## Error Handling

The plugin includes comprehensive error handling:
- Graceful degradation when system commands fail
- Logging of errors and warnings
- JSON output with status indication
- Safe parsing of system files
- Input validation for monitoring parameters
- Proper signal handling for graceful shutdown

## Monitoring Loop Details

### Operation Modes

1. **Single Extraction Mode**: When `monitor-interval` is 0, the plugin runs once and exits
2. **Monitoring Loop Mode**: When `monitor-interval` > 0, the plugin runs continuously
3. **No Limit Mode**: When trigger percentage is 0, that metric is not monitored

### Behavior

- The plugin runs an infinite loop until interrupted (Ctrl+C)
- Each cycle checks the specified metrics against their thresholds
- When a threshold is exceeded, the complete system data is output in JSON format
- The plugin logs all trigger events and maintains a log of the monitoring status
- CPU and memory trigger percentages are mandatory parameters
- Values outside the 0-100 range are rejected with validation errors

## Security Notes

- Requires appropriate permissions to read system files and execute commands
- Process information may be restricted based on user permissions
- No sensitive data is collected or transmitted
- Monitoring loop runs indefinitely until manually stopped