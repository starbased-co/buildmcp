# Meta∞MCP

Meta∞MCP is a Terminal User Interface (TUI) for managing MCP (Model Context Protocol) servers through the MetaMCP web application API.

## Overview

Meta∞MCP provides:

- **Interactive TUI**: Browse, create, delete, and bulk import MCP server configurations
- **API Client**: Programmatic access to MetaMCP's tRPC endpoints
- **Session Management**: Cookie-based authentication with environment variable support

### Supported Operations

| Operation | Method | Endpoint | Description |
|-----------|--------|----------|-------------|
| List | GET | `frontend.mcpServers.list` | Retrieve all MCP servers |
| Create | POST | `frontend.mcpServers.create` | Add a new MCP server |
| Delete | POST | `frontend.mcpServers.delete` | Remove server by UUID |
| Bulk Import | POST | `frontend.mcpServers.bulkImport` | Import multiple servers from JSON |

## Installation

```bash
# From project root
uv sync

# Or add to existing project
uv add buildmcp
```

## Authentication

Meta∞MCP requires a session token from MetaMCP's better-auth authentication system.

### Method 1: Environment Variable (Recommended)

```bash
export METAMCP_SESSION_TOKEN="your-session-token-here"
uv run metamcp
```

### Method 2: Cookie File

```bash
# Save token to file
echo "your-session-token-here" > ~/.metamcp-session

# Pass file path
uv run metamcp --cookie-file ~/.metamcp-session
```

### Extracting Session Token

1. Log into MetaMCP web interface (usually `http://localhost:12008`)
2. Open browser DevTools → Application/Storage → Cookies
3. Copy value of `better-auth.session_token`
4. URL-decode the value if needed

Example cookie value:
```
[REDACTED_SESSION_TOKEN_1]
```

## TUI Usage

### Launch

```bash
# Default (localhost:12008)
uv run metamcp

# Custom instance
uv run metamcp --base-url http://192.168.1.100:12008

# With cookie file
uv run metamcp --cookie-file ~/.metamcp-session
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit the application |
| `r` | Refresh | Reload server list |
| `c` | Create | Open create server form |
| `d` | Delete | Delete selected server |
| `i` | Import | Open bulk import screen |
| `↑`/`↓` | Navigate | Move cursor in table |
| `Esc` | Cancel | Return to previous screen |
| `Ctrl+S` | Submit | Submit active form |

### Creating a Server

Press `c` to open the create form. Fill in the fields:

**STDIO Server Example:**
```
Name:         my-stdio-server
Type:         STDIO
Command:      npx
Args (JSON):  ["-y", "@modelcontextprotocol/server-filesystem"]
Description:  Local filesystem server
```

**HTTP Server Example:**
```
Name:          github-copilot
Type:          STREAMABLE_HTTP
URL:           https://api.githubcopilot.com/mcp
Bearer Token:  ghp_YourGitHubTokenHere
Description:   GitHub Copilot MCP integration
```

**SSE Server Example:**
```
Name:          sse-server
Type:          SSE
URL:           https://api.example.com/events
Description:   Server-Sent Events endpoint
```

### Bulk Import

Press `i` to open the bulk import screen. Paste JSON in either format:

**Full Format:**
```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp",
      "headers": {
        "Authorization": "Bearer ghp_token"
      }
    }
  }
}
```

**Compact Format:**
```json
{
  "filesystem": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem"]
  }
}
```

Press `Ctrl+S` to submit the import.

### Deleting a Server

1. Use `↑`/`↓` to select a server in the table
2. Press `d` to delete
3. Confirm the deletion

The server will be permanently removed from MetaMCP.

## API Client Usage

### Python API

```python
from buildmcp.metamcp import get_client

# Initialize client
client = get_client(
    base_url="http://localhost:12008",
    cookie_file=None  # Or Path to cookie file
)

# List all servers
servers = client.list_servers()
for server in servers:
    print(f"{server.name} ({server.type}): {server.uuid}")

# Create a new server
new_server = client.create_server(
    name="my-server",
    server_type="STDIO",
    command="npx",
    args=["-y", "@scope/package"],
    description="My custom server"
)
print(f"Created: {new_server.uuid}")

# Delete a server
success = client.delete_server(uuid="server-uuid-here")
print(f"Deleted: {success}")

# Bulk import
servers_config = {
    "server1": {
        "type": "stdio",
        "command": "node",
        "args": ["server.js"]
    },
    "server2": {
        "type": "http",
        "url": "https://api.example.com/mcp"
    }
}
imported_count = client.bulk_import(servers_config)
print(f"Imported {imported_count} servers")
```

### Server Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `STDIO` | Standard input/output | `command`, `args` |
| `STREAMABLE_HTTP` | HTTP streaming | `url`, optional `bearerToken` |
| `SSE` | Server-Sent Events | `url` |

### Data Models

**MetaMCPServer:**
```python
@attrs.define
class MetaMCPServer:
    name: str              # Server identifier
    type: str              # STDIO, STREAMABLE_HTTP, SSE
    uuid: str | None       # Server UUID (from API)
    description: str       # Optional description
    command: str           # Command for STDIO servers
    args: list[str]        # Arguments for STDIO servers
    env: dict[str, str]    # Environment variables
    url: str               # URL for HTTP/SSE servers
    bearerToken: str       # Optional bearer token
    created_at: str | None # ISO timestamp
    user_id: str | None    # Owner user ID
```

## Architecture

### Module Structure

```
src/buildmcp/
├── metamcp.py        # API client and data models
└── metamcp_tui.py    # Textual TUI application
```

### Request Flow

```
TUI/API Client
    ↓
MetaMCPClient._make_request()
    ↓
HTTP Request (httpx)
    ↓
MetaMCP tRPC API
    ↓
Database (better-auth session + MCP servers)
```

### HAR Files

The `har/` directory contains HTTP Archive files capturing the 4 API operations:

- `list.har` - GET request example
- `create.har` - POST create request
- `delete.har` - POST delete request
- `bulkImport.har` - POST bulk import request

These files document the exact API format and can be used for testing or API exploration.

## Troubleshooting

### Session Token Issues

**Error:** `Session token not found`

**Solution:**
1. Verify token is set: `echo $METAMCP_SESSION_TOKEN`
2. Re-extract token from browser cookies
3. Check for URL encoding issues (token should be decoded)
4. Ensure cookie file exists and is readable

### Connection Errors

**Error:** `HTTP Error 401: Unauthorized`

**Solution:**
- Session token expired, extract fresh token
- Token was copied incorrectly (check for truncation)

**Error:** `Request Error: All connection attempts failed`

**Solution:**
- MetaMCP instance not running
- Wrong base URL (check port number)
- Firewall blocking connection

### Import Errors

**Error:** `Invalid JSON`

**Solution:**
- Validate JSON syntax in online validator
- Check for trailing commas
- Ensure proper quote escaping

**Error:** `Failed to bulk import`

**Solution:**
- Check server configuration format matches MetaMCP schema
- Verify required fields are present
- Review MetaMCP logs for detailed error

## Development

### Running Tests

```bash
# Not yet implemented
uv run pytest tests/
```

### Adding New Operations

To add a new API operation:

1. **Capture HAR file**: Use browser DevTools to save request
2. **Update `MetaMCPClient`**: Add method in `metamcp.py`
3. **Add TUI screen**: Create new screen class in `metamcp_tui.py`
4. **Add keybinding**: Update `BINDINGS` and `action_*` method
5. **Update docs**: Document new operation here

### Example: Adding Update Operation

```python
# metamcp.py
def update_server(self, uuid: str, **updates) -> MetaMCPServer:
    """Update an existing MCP server."""
    payload = {"0": {"uuid": uuid, **updates}}
    result = self._make_request("POST", "update?batch=1", payload)
    # Parse and return updated server
```

## Related Files

- `metamcp_deploy.py` - Original proof-of-concept deployment script
- `docs/metamcp-deploy.md` - Documentation for deployment script
- `har/` - HTTP Archive files with API request examples
- `src/buildmcp/builder.py` - Main buildmcp CLI tool

## License

Part of the buildmcp project. See project README for license information.
