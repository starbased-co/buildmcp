"""Build and deploy MCP server configurations from templates."""

from buildmcp.builder import MCPBuilder, main
from buildmcp.checksum import (
    check_mcp_lock,
    hash_json_data,
    hash_json_paths,
    hash_profiles,
    read_dot_mcp,
    read_json_path,
    write_dot_mcp,
    write_json_path,
    write_mcp_lock,
)

__version__ = "0.1.0"

__all__ = [
    "MCPBuilder",
    "main",
    "check_mcp_lock",
    "hash_json_data",
    "hash_json_paths",
    "hash_profiles",
    "read_dot_mcp",
    "read_json_path",
    "write_dot_mcp",
    "write_json_path",
    "write_mcp_lock",
    "__version__",
]
