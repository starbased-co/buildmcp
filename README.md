# buildmcp

**Complete toolkit for managing MCP (Model Context Protocol) server configurations**

Build template-based configs, manage servers interactively, and automate deployments - all from one unified toolset.

---

## 🚀 Quick Start

**[→ Get started in 5 minutes](./QUICKSTART.md)**

```bash
# Install
git clone https://github.com/starbased-co/buildmcp.git
cd buildmcp && uv sync

# Choose your tool:
uv run buildmcp --dry-run      # Template builder
uv run metamcp                 # Interactive TUI
uv run metamcp-cli server:list # Command-line interface
```

---

## 🛠️ Tool Suite

### buildmcp - Configuration Builder

Template-based MCP server configuration builder with environment variable substitution and checksums.

**Best for:** Building configs from templates, deploying to multiple targets, managing environment-specific configs

```bash
# Preview build
uv run buildmcp --dry-run

# Deploy to targets
uv run buildmcp

# Force write (skip checksums)
uv run buildmcp --force
```

**Features:**
- ✅ Template composition system
- ✅ Environment variable substitution (`${VAR_NAME}`)
- ✅ SHA-256 checksum change detection
- ✅ Lock file tracking
- ✅ Multiple deployment targets
- ✅ Profile-based configurations

[📖 Full buildmcp Documentation](./docs/buildmcp.md)

---

### Meta∞MCP TUI - Interactive Terminal Interface

Full-featured terminal UI for browsing and managing MCP servers and namespaces.

**Best for:** Visual exploration, interactive management, namespace organization, tool status management

```bash
# Launch TUI
export METAMCP_SESSION_TOKEN="your-token"
uv run metamcp
```

**Features:**
- ✅ Server browsing and management
- ✅ Namespace exploration with tools view
- ✅ Interactive status toggling
- ✅ Bulk import interface
- ✅ Real-time updates
- ✅ Keyboard-driven navigation

**Keyboard Shortcuts:**
- `q` - Quit
- `r` - Refresh
- `c` - Create
- `d` - Delete
- `i` - Import
- `s` - Toggle server status
- `t` - Toggle tool status

[📖 Full TUI Documentation](./docs/metamcp.md)

---

### metamcp-cli - Command-Line Interface

Scriptable CLI for all MetaMCP operations with full JSON input support.

**Best for:** Automation, CI/CD pipelines, shell scripts, batch operations

```bash
# List servers
metamcp-cli server:list

# Create from JSON (stdin)
echo '{"name": "test", "type": "STDIO", "command": "npx"}' | \
  metamcp-cli server:create --stdin

# Bulk import
cat servers.json | metamcp-cli server:bulk-import --stdin

# Update namespace tools
metamcp-cli namespace:update-tool-status \
  --namespace-uuid "..." \
  --tool-uuid "..." \
  --server-uuid "..." \
  --status "ACTIVE"
```

**Features:**
- ✅ All server operations (list, create, delete, import)
- ✅ Namespace management (list, get, tools, status)
- ✅ JSON input (file, stdin, pipe)
- ✅ Rich table output
- ✅ Scriptable and pipeable
- ✅ Error handling with exit codes

[📖 Full CLI Documentation](./docs/metamcp-cli.md)

---

## 📋 Features Comparison

| Feature | buildmcp | TUI | CLI |
|---------|----------|-----|-----|
| Template system | ✅ | ❌ | ❌ |
| Environment substitution | ✅ | ❌ | ❌ |
| Server management | ❌ | ✅ | ✅ |
| Namespace management | ❌ | ✅ | ✅ |
| Tool status control | ❌ | ✅ | ✅ |
| Visual interface | ❌ | ✅ | ❌ |
| JSON input/output | ✅ | ✅ | ✅ |
| Automation friendly | ✅ | ❌ | ✅ |
| Real-time updates | ❌ | ✅ | ❌ |
| Bulk operations | ✅ | ✅ | ✅ |

---

## 📚 Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - Get started in 5 minutes
- **[USAGE.md](./USAGE.md)** - Complete usage guide with workflows
- **[docs/metamcp.md](./docs/metamcp.md)** - Meta∞MCP TUI guide
- **[docs/metamcp-cli.md](./docs/metamcp-cli.md)** - CLI reference
- **[CLAUDE.md](./CLAUDE.md)** - Project context for Claude
- **[MCP_FORMAT_SPECIFICATION.md](./MCP_FORMAT_SPECIFICATION.md)** - MCP format details

---

## 🏗️ Installation

### Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Install from Source

```bash
# Clone repository
git clone https://github.com/starbased-co/buildmcp.git
cd buildmcp

# Install dependencies
uv sync

# Verify installation
uv run buildmcp --help
uv run metamcp --help
uv run metamcp-cli --help
```

### Development Install

```bash
# Install in editable mode
uv pip install -e .

# Run tests
uv run pytest

# Run with verbose
uv run buildmcp --verbose --dry-run
```

---

## 🎯 Common Workflows

### Workflow 1: Template-Based Deployment

```bash
# 1. Edit templates
vim ~/.config/nix/config/claude/mcp.json

# 2. Preview
uv run buildmcp --dry-run

# 3. Deploy
uv run buildmcp

# 4. Verify
cat ~/.claude/mcp.json
```

### Workflow 2: Import to MetaMCP

```bash
# Import existing Claude config
cat ~/.claude/mcp.json | \
  jq '.mcpServers' | \
  metamcp-cli server:bulk-import --stdin

# Browse in TUI
uv run metamcp
```

### Workflow 3: Namespace Management

```bash
# List namespaces
metamcp-cli namespace:list

# Get tools
metamcp-cli namespace:tools --uuid "ns-abc123..."

# Toggle tool status in TUI
uv run metamcp
# → Navigate to namespace → Tools → Press 't'
```

### Workflow 4: Automated Provisioning

```bash
#!/bin/bash
# Create servers from list
for name in $(cat servers.txt); do
  echo "{\"name\": \"$name\", \"type\": \"STDIO\"}" | \
    metamcp-cli server:create --stdin
done
```

---

## 🔧 Configuration

### buildmcp Config

Location: `~/.config/nix/config/claude/mcp.json` (or custom with `--mcp-json`)

```json
{
  "mcpServers": {
    "base-server": {
      "command": "npx",
      "args": ["-y", "@scope/package"]
    }
  },
  "templates": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  },
  "profiles": {
    "default": ["github"],
    "minimal": []
  },
  "targets": {
    "default": "~/.claude/mcp.json",
    "custom": {
      "read": "cat ~/custom-mcp.json",
      "write": "cat > ~/custom-mcp.json"
    }
  }
}
```

### Meta∞MCP Authentication

```bash
# Set session token (from browser DevTools)
export METAMCP_SESSION_TOKEN="your-session-token"

# Or use cookie file
echo "your-token" > ~/.metamcp
chmod 600 ~/.metamcp

uv run metamcp --cookie-file ~/.metamcp
metamcp-cli --cookie-file ~/.metamcp server:list
```

---

## 📖 CLI Reference

### buildmcp

```bash
buildmcp [OPTIONS]

Options:
  --mcp-json PATH     Config file (default: ~/.claude/mcp.json)
  --verbose          Show detailed output
  --dry-run          Preview without writing
  --force            Ignore checksums, redeploy all
  --no-check-env     Skip env var validation
```

### metamcp (TUI)

```bash
metamcp [OPTIONS]

Options:
  --base-url URL        MetaMCP server URL (default: http://localhost:12008)
  --cookie-file PATH    Session token file

Keyboard:
  q     Quit
  r     Refresh
  c     Create
  d     Delete
  i     Import
  s     Toggle server status (in namespace view)
  t     Toggle tool status (in namespace view)
```

### metamcp-cli

```bash
metamcp-cli <command-group>:<action> [OPTIONS]

Server Commands:
  server:list                          List all servers
  server:create [--name N --type T]    Create server
  server:delete --uuid UUID            Delete server
  server:bulk-import [-f FILE]         Bulk import

Namespace Commands:
  namespace:list                       List namespaces
  namespace:get --uuid UUID            Get details
  namespace:tools --uuid UUID          List tools
  namespace:update-tool-status         Update tool
  namespace:update-server-status       Update server

Options:
  -f, --file PATH    JSON file input
  --stdin            Read from stdin
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/buildmcp

# Run specific test
uv run pytest tests/test_builder.py
```

---

## 🔗 Integrations

### Claude Code

```bash
# Deploy to Claude Code
uv run buildmcp

# Restart Claude Code to load config
```

### MCPNest

Deploy to [mcpnest.dev](https://mcpnest.dev/) using [mcpnest-cli](https://github.com/starbased-co/mcpnest-cli):

```bash
# Add mcpnest target
{
  "targets": {
    "mcpnest": {
      "read": "mcpnest config read",
      "write": "mcpnest config write"
    }
  },
  "profiles": {
    "mcpnest": ["linkup", "sequential-thinking"]
  }
}

# Deploy
uv run buildmcp
```

### Shell Scripts

```bash
# Use in scripts
SERVERS=$(metamcp-cli server:list --format json)
echo "$SERVERS" | jq '.[] | select(.type == "STDIO")'
```

---

## 🐛 Troubleshooting

### Authentication Issues

```bash
# Error: HTTP 401 Unauthorized
# → Get fresh token from browser DevTools
export METAMCP_SESSION_TOKEN="new-token"
```

### Connection Issues

```bash
# Cannot connect to server
# → Check server is running
curl http://localhost:12008/api/health

# → Use correct URL
uv run metamcp --base-url http://your-server:12008
```

### Build Issues

```bash
# Missing environment variables
# → Set the variable
export GITHUB_TOKEN="your-token"

# → Or skip validation
uv run buildmcp --no-check-env
```

[📖 Full Troubleshooting Guide](./USAGE.md#troubleshooting)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure tests pass: `uv run pytest`
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](./LICENSE) file

---

## 🔗 Links

- **Repository:** [github.com/starbased-co/buildmcp](https://github.com/starbased-co/buildmcp)
- **Issues:** [github.com/starbased-co/buildmcp/issues](https://github.com/starbased-co/buildmcp/issues)
- **MCPNest:** [mcpnest.dev](https://mcpnest.dev/)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

**Made with ❤️ by [starbased](https://github.com/starbased-co)**
