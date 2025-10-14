# Machine Data Extractor Plugin

A Stavily plugin for extracting system information including CPU, memory, disk, and process data from the host machine.

## Features

- **System Information**: Basic system details (hostname, platform, uptime, etc.)
- **CPU Information**: CPU count and current usage percentage
- **Memory Information**: Detailed memory and swap statistics
- **Disk Information**: Filesystem partitions and usage data
- **Process Information**: Running processes with CPU/memory usage (top 50 by CPU)

## Configuration

The plugin supports selective data extraction through configuration flags:

- `extract_cpu`: Extract CPU information
- `extract_memory`: Extract memory information
- `extract_disk`: Extract disk information
- `extract_processes`: Extract process information

By default, all extraction options are disabled. Only enabled options will be included in the output.

## Usage

### Command Line

```bash
# Extract only system information (default)
python3 main.py

# Extract CPU and memory information
python3 main.py --extract-cpu --extract-memory

# Extract all available information
python3 main.py --extract-cpu --extract-memory --extract-disk --extract-processes
```

### Plugin Configuration

Configure the plugin in `plugin.yaml`:

```yaml
configuration:
  extract_cpu: true      # Enable CPU extraction
  extract_memory: true   # Enable memory extraction
  extract_disk: false    # Disable disk extraction
  extract_processes: false # Disable process extraction
```

## Output Format

The plugin outputs JSON data with the following structure:

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

## Security Notes

- Requires appropriate permissions to read system files and execute commands
- Process information may be restricted based on user permissions
- No sensitive data is collected or transmitted