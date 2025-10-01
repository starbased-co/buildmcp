import hashlib
import json
from pathlib import Path
from typing import Any

import dpath


def read_json_path(file_path: Path, path: str = ".") -> Any:
    """Read JSON file and extract value at path.

    Args:
        file_path: Path to JSON file
        path: jq-style path expression (e.g., '.profiles.default', default '.')

    Returns:
        Value at specified path

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        KeyError: If path doesn't exist in JSON
    """
    data = json.loads(file_path.read_text())

    if path == ".":
        return data

    dpath_str = path.lstrip(".").replace(".", "/")
    try:
        return dpath.get(data, dpath_str)
    except KeyError as e:
        raise KeyError(f"Path not found: {path}") from e


def write_json_path(file_path: Path, value: Any, path: str = ".") -> None:
    """Write value to JSON file at specified path.

    Args:
        file_path: Path to JSON file
        value: Value to write
        path: jq-style path expression (e.g., '.profiles.default', default '.')

    Raises:
        OSError: If file cannot be written
    """
    if file_path.exists():
        data = json.loads(file_path.read_text())
    else:
        data = {}

    if path == ".":
        data = value
    else:
        dpath_str = path.lstrip(".").replace(".", "/")
        dpath.new(data, dpath_str, value)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data, indent=2) + "\n")


def read_dot_mcp(config_path: Path | None = None, path: str = ".") -> Any:
    """Read MCP configuration from file.

    Args:
        config_path: Path to mcp.json file (defaults to ~/.claude/mcp.json)
        path: jq-style path expression (e.g., '.profiles', default '.')

    Returns:
        Value at specified path in configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        KeyError: If path doesn't exist
    """
    if config_path is None:
        config_path = Path.home() / ".claude" / "mcp.json"
    return read_json_path(config_path, path)


def write_dot_mcp(data: Any, config_path: Path | None = None, path: str = ".") -> None:
    """Write MCP configuration to file.

    Args:
        data: Configuration data to write
        config_path: Path to mcp.json file (defaults to ~/.claude/mcp.json)
        path: jq-style path expression (e.g., '.profiles', default '.')

    Raises:
        OSError: If file cannot be written
        KeyError: If intermediate path doesn't exist
    """
    if config_path is None:
        config_path = Path.home() / ".claude" / "mcp.json"
    write_json_path(config_path, data, path)


def hash_profiles(config: dict[str, Any]) -> dict[str, str]:
    """Generate hashes for all profiles in config.

    Args:
        config: MCP configuration dict containing profiles

    Returns:
        Dict mapping profile names to their hashes
    """
    profile_hashes = {}
    if "profiles" in config:
        for profile_name, profile_data in config["profiles"].items():
            profile_hashes[profile_name] = hash_json_data(profile_data)
    return profile_hashes


def write_mcp_lock(config_path: Path | None = None) -> None:
    """Generate lock file with hashes of profile configurations.

    Args:
        config_path: Path to mcp.json file (defaults to ~/.claude/mcp.json)

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        OSError: If lock file cannot be written
    """
    if config_path is None:
        config_path = Path.home() / ".claude" / "mcp.json"

    config = read_dot_mcp(config_path)
    profile_hashes = hash_profiles(config)

    lock_path = config_path.with_suffix(".lock")
    lock_path.write_text(json.dumps(profile_hashes, indent=2) + "\n")


def check_mcp_lock(config_path: Path | None = None) -> dict[str, bool]:
    """Check if profile hashes match lock file.

    Args:
        config_path: Path to mcp.json file (defaults to ~/.claude/mcp.json)

    Returns:
        Dict mapping profile names to match status (True if unchanged, False if changed)

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if config_path is None:
        config_path = Path.home() / ".claude" / "mcp.json"

    config = read_dot_mcp(config_path)
    current_hashes = hash_profiles(config)

    lock_path = config_path.with_suffix(".lock")
    if not lock_path.exists():
        return {profile: False for profile in current_hashes}

    locked_hashes = json.loads(lock_path.read_text())

    return {
        profile: current_hashes.get(profile) == locked_hashes.get(profile)
        for profile in current_hashes
    }


def hash_json_data(data: Any, algorithm: str = "sha256") -> str:
    """Generate hash of JSON data for change detection.

    Args:
        data: Data to hash (any JSON-serializable type)
        algorithm: Hash algorithm to use ('sha256' or 'md5')

    Returns:
        Hexadecimal hash digest string
    """
    normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hash_func = hashlib.sha256 if algorithm == "sha256" else hashlib.md5
    return hash_func(normalized.encode("utf-8")).hexdigest()


def hash_json_paths(
    file_path: Path,
    paths: list[str],
    algorithm: str = "sha256"
) -> str:
    """Generate combined hash from multiple JSON paths.

    Args:
        file_path: Path to JSON file
        paths: List of jq-style path expressions to hash
        algorithm: Hash algorithm to use ('sha256' or 'md5')

    Returns:
        Hexadecimal hash digest of combined paths

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        KeyError: If any path doesn't exist

    Example:
        hash = hash_json_paths(
            Path("config.json"),
            [".profiles.default", ".mcpServers"]
        )
    """
    values = [read_json_path(file_path, path) for path in paths]
    return hash_json_data(values, algorithm)
