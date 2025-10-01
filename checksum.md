# checksum.py

Utilities for managing MCP configuration checksums and lock files.

## Overview

This module provides functions for:
- Reading/writing JSON files with jq-style path expressions
- Generating SHA256/MD5 hashes of any JSON data
- Hashing multiple JSON paths together for combined change detection
- Creating lock files to track MCP profile changes
- Validating profiles against lock files

## Core Functions

### JSON Path Operations

#### `read_json_path(file_path, path=".")`

Read value from JSON file at specified path.

**Args:**
- `file_path: Path` - Path to JSON file
- `path: str` - jq-style path expression (default: `"."`)

**Returns:** Value at specified path

**Example:**
```python
from pathlib import Path

# Read entire file
data = read_json_path(Path("config.json"))

# Read nested value
profile = read_json_path(Path("config.json"), ".profiles.default")
```

#### `write_json_path(file_path, value, path=".")`

Write value to JSON file at specified path.

**Args:**
- `file_path: Path` - Path to JSON file
- `value: Any` - Value to write
- `path: str` - jq-style path expression (default: `"."`)

**Example:**
```python
# Write entire file
write_json_path(Path("config.json"), {"key": "value"})

# Write nested value
write_json_path(Path("config.json"), ["server1", "server2"], ".profiles.default")
```

### MCP Configuration Operations

#### `read_dot_mcp(config_path=None, path=".")`

Read MCP configuration from `~/.claude/mcp.json` or custom path.

**Args:**
- `config_path: Path | None` - Path to mcp.json (default: `~/.claude/mcp.json`)
- `path: str` - jq-style path expression (default: `"."`)

**Returns:** Value at specified path

**Example:**
```python
# Read entire config
config = read_dot_mcp()

# Read just profiles
profiles = read_dot_mcp(path=".profiles")

# Read specific profile
default_profile = read_dot_mcp(path=".profiles.default")
```

#### `write_dot_mcp(data, config_path=None, path=".")`

Write MCP configuration to file.

**Args:**
- `data: Any` - Data to write
- `config_path: Path | None` - Path to mcp.json (default: `~/.claude/mcp.json`)
- `path: str` - jq-style path expression (default: `"."`)

**Example:**
```python
# Write entire config
write_dot_mcp({"profiles": {}})

# Update specific profile
write_dot_mcp(["server1", "server2"], path=".profiles.default")
```

### Hashing Functions

#### `hash_json_data(data, algorithm="sha256")`

Generate hash of JSON data for change detection.

**Args:**
- `data: Any` - Data to hash (any JSON-serializable type)
- `algorithm: str` - Hash algorithm (`"sha256"` or `"md5"`)

**Returns:** Hexadecimal hash digest string

**Example:**
```python
# Hash a list
servers = ["server1", "server2", "server3"]
checksum = hash_json_data(servers)
# Returns: "a1b2c3d4..."

# Hash a dict
config = {"timeout": 30, "retries": 3}
checksum = hash_json_data(config)

# Hash a string
checksum = hash_json_data("some value")

# Use MD5 for faster hashing
checksum_md5 = hash_json_data(servers, algorithm="md5")
```

#### `hash_json_paths(file_path, paths, algorithm="sha256")`

Generate combined hash from multiple JSON paths.

**Args:**
- `file_path: Path` - Path to JSON file
- `paths: list[str]` - List of jq-style path expressions to hash
- `algorithm: str` - Hash algorithm (`"sha256"` or `"md5"`)

**Returns:** Hexadecimal hash digest of combined paths

**Example:**
```python
from pathlib import Path

# Hash multiple paths from a file
checksum = hash_json_paths(
    Path("config.json"),
    [".profiles.default", ".mcpServers", ".globalSettings"]
)

# Hash single path
checksum = hash_json_paths(
    Path("config.json"),
    [".profiles.default"]
)

# This is useful for tracking changes to multiple related fields
checksum = hash_json_paths(
    Path.home() / ".claude/mcp.json",
    [".profiles.production", ".mcpServers"]
)
```

#### `hash_profiles(config)`

Generate hashes for all profiles in MCP config.

**Args:**
- `config: dict[str, Any]` - MCP configuration dict

**Returns:** Dict mapping profile names to SHA256 hashes

**Example:**
```python
config = {
    "profiles": {
        "default": ["server1", "server2"],
        "minimal": ["server1"]
    }
}

hashes = hash_profiles(config)
# Returns: {
#   "default": "a1b2c3...",
#   "minimal": "d4e5f6..."
# }
```

### Lock File Operations

#### `write_mcp_lock(config_path=None)`

Generate lock file with hashes of profile configurations.

Creates a `.lock` file next to the config file containing hashes of all profiles.

**Args:**
- `config_path: Path | None` - Path to mcp.json (default: `~/.claude/mcp.json`)

**Example:**
```python
# Create ~/.claude/mcp.lock
write_mcp_lock()

# Create lock file for custom config
write_mcp_lock(Path("/path/to/custom.json"))
```

**Output format** (`mcp.lock`):
```json
{
  "default": "a1b2c3d4e5f6...",
  "minimal": "f6e5d4c3b2a1..."
}
```

#### `check_mcp_lock(config_path=None)`

Check if profile hashes match lock file.

**Args:**
- `config_path: Path | None` - Path to mcp.json (default: `~/.claude/mcp.json`)

**Returns:** Dict mapping profile names to match status
- `True` if profile unchanged since lock
- `False` if profile changed or no lock file exists

**Example:**
```python
status = check_mcp_lock()
# Returns: {
#   "default": True,   # unchanged
#   "minimal": False   # changed
# }

# Check for changes
if not all(status.values()):
    changed = [p for p, ok in status.items() if not ok]
    print(f"Changed profiles: {changed}")
```

## Path Expression Syntax

Paths use jq-style dot notation:

| Expression | Description | Example |
|------------|-------------|---------|
| `.` | Root (entire file) | `read_dot_mcp(path=".")` |
| `.profiles` | Top-level key | `read_dot_mcp(path=".profiles")` |
| `.profiles.default` | Nested key | `read_dot_mcp(path=".profiles.default")` |
| `.a.b.c` | Deep nesting | `read_json_path(file, ".a.b.c")` |

## Workflow Examples

### Generate and Validate Lock File

```python
from pathlib import Path
from checksum import write_mcp_lock, check_mcp_lock

# Step 1: Generate initial lock file
write_mcp_lock()

# Step 2: Make changes to profiles...
# (user edits ~/.claude/mcp.json)

# Step 3: Check for changes
status = check_mcp_lock()

if all(status.values()):
    print("No profile changes detected")
else:
    changed = [p for p, ok in status.items() if not ok]
    print(f"Profiles changed: {', '.join(changed)}")

    # Regenerate lock file
    write_mcp_lock()
```

### Compare Specific Profile

```python
from checksum import read_dot_mcp, hash_json_data, read_json_path
from pathlib import Path

# Read current profile
current = read_dot_mcp(path=".profiles.default")
current_hash = hash_json_data(current)

# Read locked hash
lock_data = read_json_path(Path.home() / ".claude/mcp.lock")
locked_hash = lock_data["default"]

if current_hash == locked_hash:
    print("Profile unchanged")
else:
    print("Profile modified")
```

### Custom Config Location

```python
from pathlib import Path

custom_config = Path("/etc/mcp/config.json")

# Generate lock file at /etc/mcp/config.lock
write_mcp_lock(custom_config)

# Check status
status = check_mcp_lock(custom_config)
```

### Track Multiple JSON Paths

```python
from pathlib import Path
from checksum import hash_json_paths

config_file = Path.home() / ".claude/mcp.json"

# Hash multiple related fields together
checksum = hash_json_paths(
    config_file,
    [".profiles.default", ".mcpServers", ".globalSettings"]
)

# Store checksum for later comparison
previous_checksum = checksum

# After changes...
new_checksum = hash_json_paths(
    config_file,
    [".profiles.default", ".mcpServers", ".globalSettings"]
)

if new_checksum != previous_checksum:
    print("Configuration changed")
```

## Implementation Notes

### Hash Normalization

`hash_json_data()` normalizes JSON before hashing:
- `sort_keys=True` ensures consistent key ordering
- `separators=(',', ':')` removes whitespace
- This ensures identical data produces identical hashes regardless of formatting

### Multi-Path Hashing

`hash_json_paths()` reads multiple paths and hashes them as a combined array:
- Paths are read in order and combined into a list
- The entire list is hashed as a single unit
- Changing any path value or reordering paths produces different hash

### Lock File Format

Lock files use same basename with `.lock` extension:
- `~/.claude/mcp.json` → `~/.claude/mcp.lock`
- `/path/to/config.json` → `/path/to/config.lock`

### Missing Lock Files

`check_mcp_lock()` returns `False` for all profiles when lock file doesn't exist, indicating all profiles should be considered changed.
