# Meta∞MCP CLI

Command-line interface for managing MCP servers and namespaces via the MetaMCP API.

## Installation

```bash
uv sync
```

The CLI is available as `metamcp-cli` command.

## Authentication

Set your session token:

```bash
export METAMCP_SESSION_TOKEN="your-session-token"
```

Or use a cookie file:

```bash
echo "your-session-token" > ~/.metamcp
metamcp-cli --cookie-file ~/.metamcp server:list
```

## Server Commands

### List Servers

```bash
metamcp-cli server:list
```

### Create Server

**From CLI arguments:**

```bash
metamcp-cli server:create \
  --name "my-server" \
  --server-type "STDIO" \
  --command "npx" \
  --description "My test server"
```

**From JSON file:**

```bash
metamcp-cli server:create -f server.json
```

**From stdin:**

```bash
echo '{"name": "test-server", "type": "STDIO", "command": "npx", "args": ["-y", "@test/server"]}' | \
  metamcp-cli server:create --stdin
```

**Pipe from another command:**

```bash
cat servers.json | metamcp-cli server:create
```

### Delete Server

```bash
metamcp-cli server:delete --uuid "server-uuid-here"
```

### Bulk Import

**From file:**

```bash
metamcp-cli server:bulk-import -f servers.json
```

Expected format:

```json
{
  "mcpServers": {
    "server1": {
      "command": "npx",
      "args": ["-y", "@scope/package"]
    },
    "server2": {
      "url": "https://api.example.com/mcp"
    }
  }
}
```

**From stdin:**

```bash
cat mcp-config.json | metamcp-cli server:bulk-import --stdin
```

## Namespace Commands

### List Namespaces

```bash
metamcp-cli namespace:list
```

### Get Namespace Details

**With servers only:**

```bash
metamcp-cli namespace:get --uuid "namespace-uuid"
```

**With servers and tools:**

```bash
metamcp-cli namespace:get --uuid "namespace-uuid" --show-tools
```

**Tools only:**

```bash
metamcp-cli namespace:get --uuid "namespace-uuid" --no-show-servers --show-tools
```

### List Namespace Tools

```bash
metamcp-cli namespace:tools --uuid "namespace-uuid"
```

### Update Tool Status

```bash
metamcp-cli namespace:update-tool-status \
  --namespace-uuid "namespace-uuid" \
  --tool-uuid "tool-uuid" \
  --server-uuid "server-uuid" \
  --status "INACTIVE"
```

Valid statuses: `ACTIVE`, `INACTIVE`

### Update Server Status in Namespace

```bash
metamcp-cli namespace:update-server-status \
  --namespace-uuid "namespace-uuid" \
  --server-uuid "server-uuid" \
  --status "ACTIVE"
```

## JSON Input Methods

The CLI supports three methods for providing JSON input:

### 1. File Input (`-f` or `--file`)

```bash
metamcp-cli server:create -f config.json
```

### 2. Explicit Stdin (`--stdin`)

```bash
echo '{"name": "server", "type": "STDIO"}' | metamcp-cli server:create --stdin
```

### 3. Implicit Stdin (pipe detection)

```bash
cat config.json | metamcp-cli server:create
```

The CLI automatically detects piped input when:
- No `-f` flag is provided
- No required CLI arguments are provided
- stdin is not a TTY

## Examples

### Create and Configure Server

```bash
# Create server from JSON
echo '{
  "name": "github-mcp",
  "type": "STDIO",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {"GITHUB_TOKEN": "your-token"}
}' | metamcp-cli server:create --stdin

# List to verify
metamcp-cli server:list
```

### Manage Namespace Tools

```bash
# Get namespace UUID
metamcp-cli namespace:list

# View all tools
metamcp-cli namespace:tools --uuid "your-namespace-uuid"

# Disable a specific tool
metamcp-cli namespace:update-tool-status \
  --namespace-uuid "your-namespace-uuid" \
  --tool-uuid "tool-uuid-here" \
  --server-uuid "server-uuid-here" \
  --status "INACTIVE"
```

### Bulk Operations

```bash
# Export existing servers to JSON
metamcp-cli server:list --format json > backup.json

# Import from Claude Code config
cat ~/.claude/mcp.json | \
  jq '.mcpServers' | \
  metamcp-cli server:bulk-import --stdin
```

## Output Formatting

All commands use Rich tables for formatted output with:
- Color-coded columns
- Truncated long values
- Total counts

Example server list output:

```
┌──────────────────────────────────────┬─────────────┬────────┬─────────────────┐
│ UUID                                 │ Name        │ Type   │ URL/Command     │
├──────────────────────────────────────┼─────────────┼────────┼─────────────────┤
│ abc123...                            │ github-mcp  │ STDIO  │ npx             │
│ def456...                            │ weather-api │ SSE    │ https://api...  │
└──────────────────────────────────────┴─────────────┴────────┴─────────────────┘

Total: 2 servers
```

## Error Handling

The CLI provides clear error messages:

```bash
# Missing required argument
$ metamcp-cli server:create --name "test"
Error: name and server_type are required when not using JSON input

# Invalid status value
$ metamcp-cli namespace:update-tool-status ... --status "UNKNOWN"
Error: status must be ACTIVE or INACTIVE

# API errors
$ metamcp-cli server:create -f bad.json
Error: HTTP Error 400: Invalid server configuration
```

## Integration with Other Tools

### With jq

```bash
# Extract specific servers
metamcp-cli server:list --format json | \
  jq '.[] | select(.type == "STDIO")'

# Transform config format
cat legacy-config.json | \
  jq '{mcpServers: .servers}' | \
  metamcp-cli server:bulk-import --stdin
```

### With buildmcp

```bash
# Export buildmcp template to MetaMCP
buildmcp --dry-run --format json | \
  jq '.mcpServers' | \
  metamcp-cli server:bulk-import --stdin
```

### In Scripts

```bash
#!/bin/bash

# Create server and capture UUID
UUID=$(echo '{
  "name": "temp-server",
  "type": "STDIO",
  "command": "node",
  "args": ["server.js"]
}' | metamcp-cli server:create --stdin | \
  grep UUID | awk '{print $2}')

# Use the UUID
echo "Created server: $UUID"

# Clean up
metamcp-cli server:delete --uuid "$UUID"
```

## See Also

- [Meta∞MCP TUI](./metamcp.md) - Interactive terminal interface
- [buildmcp](../README.md) - Template-based configuration builder
