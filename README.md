# `buildmcp`

Build targeted MCP (Model Context Protocol) server configurations from templates with change detection.

Deploy MCP servers locally or to the cloud with [mcpnest.dev](https://mcpnest.dev/) using [mcpnest-cli](https://github.com/starbased-co/mcpnest-cli).

## Features

- **Template composition** - Merge base servers with reusable templates into profiles
- **Smart deployment** - SHA-256 checksums prevent unnecessary writes
- **Flexible targets** - Deploy to JSON files, shell commands, or cloud services
- **Environment substitution** - `${VAR_NAME}` syntax throughout configs
- **Lock file tracking** - `.lock` file tracks configuration state

## Installation

Requires Python 3.12+

```bash
# Recommended: install with uv
uv tool install buildmcp

# Alternative: pipx
pipx install buildmcp

# Development install
git clone https://github.com/yourusername/buildmcp
cd buildmcp
uv sync
```

## Quick Start

1. Create `~/.claude/mcp.json`:

```json
{
  "mcpServers": {},
  "targets": {
    "claude": "~/.claude.json",
    "mcpnest": {
      "read": "mcpnest read",
      "write": "mcpnest write"
    }
  },
  "profiles": {
    "claude": ["gemini-cli", "context7"]
    "mcpnest": ["linkup", "sequential-thinking"],
  },
  "templates": {
    "gemini-cli": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "gemini-mcp-tool"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "env": {}
    }
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "linkup": {
      "command": "uvx",
      "args": ["mcp-search-linkup"],
      "env": {
        "LINKUP_API_KEY": "${LINKUP_API_KEY}"
      }
    },
  }
}
```

2. Build:

```bash
# Standard deployment
buildmcp

# Debug with verbose output
buildmcp --verbose

# Preview changes for custom config
buildmcp --mcp-json ./project/mcp.json --dry-run

# Force redeploy everything
buildmcp --force
```

## Configuration

| Section      | Purpose                                       |
| ------------ | --------------------------------------------- |
| `mcpServers` | Base servers included in all profiles         |
| `profiles`   | Named groups combining templates              |
| `targets`    | Output destinations (files or shell commands) |
| `templates`  | Reusable server configurations                |

### Environment Variables

Use `${VAR_NAME}` anywhere in configs:

- Paths: `"${HOME}/configs/mcp.json"`
- Values: `"${API_KEY}"`
- Commands: `{"write": "scp - ${REMOTE_HOST}:/etc/mcp.json"}`

## CLI Options

| Option              | Description                                        |
| ------------------- | -------------------------------------------------- |
| `--mcp-json <path>` | Custom config file (default: `~/.claude/mcp.json`) |
| `--verbose`         | Show detailed output                               |
| `--dry-run`         | Preview without writing                            |
| `--force`           | Ignore checksums, redeploy all                     |
| `--no-check-env`    | Skip missing env var warnings                      |

## Integrations

- **[mcpnest-cli](https://github.com/starbased-co/mcpnest-cli)** - Deploy and manage MCP servers with [mcpnest.dev](https://mcpnest.dev/).

## License

MIT
