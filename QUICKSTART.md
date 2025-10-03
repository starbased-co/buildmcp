# buildmcp Quickstart Guide

Get started with buildmcp in under 5 minutes.

## Install

```bash
git clone https://github.com/starbased-co/buildmcp.git
cd buildmcp
uv sync
```

## Choose Your Tool

### 🏗️ buildmcp - Template Builder

**Use when:** You want to manage configs with templates and deploy to Claude Code

```bash
# 1. Preview build
uv run buildmcp --dry-run

# 2. Deploy
uv run buildmcp

# Done! Config written to ~/.claude/mcp.json
```

### 🖥️ Meta∞MCP TUI - Interactive Interface

**Use when:** You want to browse/manage servers with a visual interface

```bash
# 1. Get your session token from browser
#    DevTools (F12) → Application → Cookies → better-auth.session_token

# 2. Export token
export METAMCP_SESSION_TOKEN="your-token-here"

# 3. Launch TUI
uv run metamcp
```

**TUI Quick Controls:**
- `Tab` - Switch between Servers/Namespaces
- `↑/↓` - Navigate list
- `Enter` - Open details
- `c` - Create
- `d` - Delete
- `r` - Refresh
- `q` - Quit

### ⌨️ metamcp-cli - Command Line

**Use when:** You want to script or automate operations

```bash
# 1. Set token
export METAMCP_SESSION_TOKEN="your-token-here"

# 2. List servers
metamcp-cli server:list

# 3. Create from JSON
echo '{
  "name": "my-server",
  "type": "STDIO",
  "command": "npx",
  "args": ["-y", "@scope/package"]
}' | metamcp-cli server:create --stdin
```

## Common Workflows

### Import Existing Config

```bash
# Import Claude Code config to MetaMCP
cat ~/.claude/mcp.json | \
  jq '.mcpServers' | \
  metamcp-cli server:bulk-import --stdin
```

### Build from Templates

```bash
# Edit config
vim ~/.config/nix/config/claude/mcp.json

# Deploy
uv run buildmcp
```

### Browse Interactively

```bash
# Launch TUI
uv run metamcp

# Navigate to Namespaces tab → Select namespace → View tools
```

## Need Help?

- **Full Guide:** [USAGE.md](./USAGE.md)
- **buildmcp Details:** [README.md](./README.md)
- **TUI Guide:** [docs/metamcp.md](./docs/metamcp.md)
- **CLI Guide:** [docs/metamcp-cli.md](./docs/metamcp-cli.md)

## Troubleshooting

### "Error: HTTP Error 401"

Your session token is missing or expired.

```bash
# Get new token from browser DevTools
export METAMCP_SESSION_TOKEN="new-token"
```

### "Missing environment variable"

buildmcp needs environment variables for substitution.

```bash
# Skip check
uv run buildmcp --no-check-env

# Or set the variable
export GITHUB_TOKEN="your-token"
```

### Can't connect to server

Make sure MetaMCP server is running on localhost:12008, or specify URL:

```bash
uv run metamcp --base-url http://your-server:12008
metamcp-cli --base-url http://your-server:12008 server:list
```

---

**Ready to dive deeper?** Read the [full USAGE guide](./USAGE.md)
