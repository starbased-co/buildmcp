# buildmcp Usage Guide

Complete guide to using buildmcp tools for managing MCP (Model Context Protocol) server configurations.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Authentication](#authentication)
- [Tool Suite](#tool-suite)
  - [buildmcp - Configuration Builder](#buildmcp---configuration-builder)
  - [Meta∞MCP TUI - Interactive Management](#metamcp-tui---interactive-management)
  - [metamcp-cli - Command Line Interface](#metamcp-cli---command-line-interface)
- [Workflows](#workflows)
- [Troubleshooting](#troubleshooting)

---

## Overview

The buildmcp suite provides three complementary tools:

| Tool | Purpose | Best For |
|------|---------|----------|
| **buildmcp** | Template-based config builder | Building configs from templates, deploying to multiple targets |
| **Meta∞MCP TUI** | Interactive terminal interface | Browsing servers/namespaces, managing status, exploring tools |
| **metamcp-cli** | Command-line interface | Scripting, automation, CI/CD pipelines |

## Installation

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

## Authentication

All Meta∞MCP tools (TUI and CLI) require authentication with a MetaMCP server.

### Getting Your Session Token

1. **Open DevTools** in your browser (F12)
2. **Navigate to Application** → **Cookies** → `http://localhost:12008` (or your server URL)
3. **Find cookie** named `better-auth.session_token`
4. **Copy the value** (it should be URL-decoded automatically)

### Setting Up Authentication

**Method 1: Environment Variable (Recommended)**

```bash
export METAMCP_SESSION_TOKEN="your-session-token-here"
```

Add to your shell config (`~/.zshrc`, `~/.bashrc`):

```bash
# MetaMCP Authentication
export METAMCP_SESSION_TOKEN="your-session-token-here"
```

**Method 2: Cookie File**

```bash
# Create cookie file
echo "your-session-token-here" > ~/.metamcp
chmod 600 ~/.metamcp

# Use with commands
metamcp --cookie-file ~/.metamcp
metamcp-cli --cookie-file ~/.metamcp server:list
```

---

## Tool Suite

### buildmcp - Configuration Builder

Template-based MCP server configuration builder with environment variable substitution and checksums.

#### Quick Start

```bash
# Preview what will be built
uv run buildmcp --dry-run

# Build and deploy
uv run buildmcp

# Force write (skip checksum check)
uv run buildmcp --force

# Verbose output
uv run buildmcp --verbose
```

#### Configuration Structure

Location: `~/.config/nix/config/claude/mcp.json`

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
    "minimal": {
      "read": "cat ~/.claude/mcp-minimal.json",
      "write": "cat > ~/.claude/mcp-minimal.json"
    }
  }
}
```

#### Features

- **Template System**: Reusable server definitions
- **Environment Variables**: `${VAR_NAME}` substitution
- **Profiles**: Named groups of templates
- **Multiple Targets**: Deploy to different destinations
- **Checksum Tracking**: Only write when changed
- **Lock Files**: Track configuration state

#### Example Workflow

```bash
# 1. Edit your config
vim ~/.config/nix/config/claude/mcp.json

# 2. Test build
uv run buildmcp --dry-run

# 3. Deploy to default target
uv run buildmcp

# 4. Check what was written
cat ~/.claude/mcp.json

# 5. View lock file (checksums)
cat ~/.config/nix/config/claude/mcp.lock
```

---

### Meta∞MCP TUI - Interactive Management

Full-featured terminal user interface for managing MCP servers and namespaces.

#### Launching

```bash
# Connect to localhost:12008
uv run metamcp

# Connect to remote server
uv run metamcp --base-url http://remote-server:12008

# Use cookie file
uv run metamcp --cookie-file ~/.metamcp
```

#### TUI Interface

```
┌─────────────────────────────────────────────────────────────────┐
│                           Meta∞MCP                              │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ ┏━━━━━━━━━┓ ┏━━━━━━━━━━━━┓                                      │
│ ┃ Servers ┃ ┃ Namespaces ┃                                      │
│ ┗━━━━━━━━━┛ ┗━━━━━━━━━━━━┛                                      │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ UUID          Name        Type    URL/Command    Created │   │
│ ├─────────────────────────────────────────────────────────┤   │
│ │ abc123...     github-mcp  STDIO   npx             2025... │   │
│ │ def456...     weather-api SSE     https://api... 2025... │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│ Total: 2 servers                                                │
└─────────────────────────────────────────────────────────────────┘
 q Quit  r Refresh  c Create  d Delete  i Import
```

#### Servers Tab

**Keyboard Shortcuts:**
- `q` - Quit application
- `r` - Refresh server list
- `c` - Create new server
- `d` - Delete selected server
- `i` - Bulk import from JSON

**Creating a Server:**

1. Press `c` to open create form
2. Fill in details:
   - Name (required)
   - Type (STDIO, STREAMABLE_HTTP, SSE)
   - URL or Command
   - Bearer Token (optional)
   - Args (JSON array)
   - Description
3. Press `Ctrl+S` or click **Create**
4. Press `Esc` to cancel

**Deleting a Server:**

1. Navigate to server with arrow keys
2. Press `d` to delete
3. Confirm deletion

**Bulk Import:**

1. Press `i` to open import screen
2. Paste JSON configuration:
   ```json
   {
     "mcpServers": {
       "server1": {
         "command": "npx",
         "args": ["-y", "@scope/package"]
       }
     }
   }
   ```
3. Press `Ctrl+S` or click **Import**

#### Namespaces Tab

```
┌─────────────────────────────────────────────────────────────────┐
│ ┏━━━━━━━━━┓ ┏━━━━━━━━━━━━┓                                      │
│ ┃ Servers ┃ ┃ Namespaces ┃                                      │
│ ┗━━━━━━━━━┛ ┗━━━━━━━━━━━━┛                                      │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ Name          Description              Servers  Created  │   │
│ ├─────────────────────────────────────────────────────────┤   │
│ │ development   Dev environment tools    5        2025...  │   │
│ │ production    Production servers       3        2025...  │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│ Total: 2 namespaces                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Opening Namespace Details:**

1. Navigate to namespace with arrow keys
2. Press `Enter` to open details

#### Namespace Details Screen

```
┌─────────────────────────────────────────────────────────────────┐
│                           Meta∞MCP                              │
└─────────────────────────────────────────────────────────────────┘
Namespace: development
Description: Development environment tools

┌─────────────────────────────────────────────────────────────────┐
│ ┏━━━━━━━━━┓ ┏━━━━━━┓                                           │
│ ┃ Servers ┃ ┃ Tools ┃                                           │
│ ┗━━━━━━━━━┛ ┗━━━━━━┛                                           │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ Name          Type    Status   URL/Command              │   │
│ ├─────────────────────────────────────────────────────────┤   │
│ │ github-mcp    STDIO   ACTIVE   npx                      │   │
│ │ weather-api   SSE     INACTIVE https://api.example.com  │   │
│ └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
 Esc Back  r Refresh  s Toggle Server Status  t Toggle Tool Status
```

**Keyboard Shortcuts:**
- `Esc` - Return to namespaces list
- `r` - Refresh namespace data
- `s` - Toggle server status (ACTIVE ↔ INACTIVE)
- `t` - Toggle tool status (ACTIVE ↔ INACTIVE)

**Managing Server Status:**

1. Navigate to server with arrow keys
2. Press `s` to toggle status
3. Status updates immediately

**Viewing Tools:**

1. Click/navigate to **Tools** tab
2. View all tools with their status
3. Press `t` to toggle tool status

```
┌─────────────────────────────────────────────────────────────────┐
│ ┏━━━━━━━━━┓ ┏━━━━━━┓                                           │
│ ┃ Servers ┃ ┃ Tools ┃                                           │
│ ┗━━━━━━━━━┛ ┗━━━━━━┛                                           │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Name              Server       Status    Override Name   │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ create_issue      github-mcp   ACTIVE                    │  │
│ │ search_repos      github-mcp   ACTIVE                    │  │
│ │ get_weather       weather-api  INACTIVE                  │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│ Total: 3 tools                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### metamcp-cli - Command Line Interface

Scriptable command-line interface for all MetaMCP operations.

#### Command Structure

```
metamcp-cli <command-group>:<action> [options]
```

**Command Groups:**
- `server` - Manage MCP servers
- `namespace` - Manage namespaces

#### Server Commands

**List All Servers**

```bash
$ metamcp-cli server:list

┌──────────────────────────────────────┬─────────────┬────────┬─────────────────┐
│ UUID                                 │ Name        │ Type   │ URL/Command     │
├──────────────────────────────────────┼─────────────┼────────┼─────────────────┤
│ abc123-def456-...                    │ github-mcp  │ STDIO  │ npx             │
│ def456-abc123-...                    │ weather-api │ SSE    │ https://api...  │
└──────────────────────────────────────┴─────────────┴────────┴─────────────────┘

Total: 2 servers
```

**Create Server (CLI Args)**

```bash
$ metamcp-cli server:create \
  --name "my-server" \
  --server-type "STDIO" \
  --command "npx" \
  --description "My test server"

✓ Created server: my-server
  UUID: abc123-def456-789
```

**Create Server (JSON File)**

```bash
# Create config file
$ cat > server.json <<EOF
{
  "name": "github-mcp",
  "type": "STDIO",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "ghp_..."
  }
}
EOF

# Import
$ metamcp-cli server:create -f server.json

✓ Created server: github-mcp
  UUID: abc123-def456-789
```

**Create Server (Stdin)**

```bash
# Explicit stdin flag
$ echo '{
  "name": "test-server",
  "type": "STDIO",
  "command": "node",
  "args": ["server.js"]
}' | metamcp-cli server:create --stdin

# Auto-detected pipe
$ cat server.json | metamcp-cli server:create

# From another command
$ buildmcp --dry-run --format json | \
  jq '.mcpServers.github' | \
  metamcp-cli server:create --stdin
```

**Delete Server**

```bash
$ metamcp-cli server:delete --uuid "abc123-def456-789"

✓ Deleted server: abc123-def456-789
```

**Bulk Import**

```bash
# From file
$ metamcp-cli server:bulk-import -f servers.json

✓ Imported 5 servers

# From stdin
$ cat ~/.claude/mcp.json | \
  jq '.mcpServers' | \
  metamcp-cli server:bulk-import --stdin

✓ Imported 12 servers
```

#### Namespace Commands

**List Namespaces**

```bash
$ metamcp-cli namespace:list

┌──────────────────────────────────────┬─────────────┬────────────────────────┐
│ UUID                                 │ Name        │ Description            │
├──────────────────────────────────────┼─────────────┼────────────────────────┤
│ ns-abc123-...                        │ development │ Dev environment tools  │
│ ns-def456-...                        │ production  │ Production servers     │
└──────────────────────────────────────┴─────────────┴────────────────────────┘

Total: 2 namespaces
```

**Get Namespace Details**

```bash
# With servers (default)
$ metamcp-cli namespace:get --uuid "ns-abc123-..."

Namespace: development
Description: Dev environment tools
UUID: ns-abc123-...

┌─────────────┬────────┬──────────┬─────────────────┐
│ Name        │ Type   │ Status   │ URL/Command     │
├─────────────┼────────┼──────────┼─────────────────┤
│ github-mcp  │ STDIO  │ ACTIVE   │ npx             │
│ weather-api │ SSE    │ INACTIVE │ https://api...  │
└─────────────┴────────┴──────────┴─────────────────┘

# With tools
$ metamcp-cli namespace:get --uuid "ns-abc123-..." --show-tools

[... servers table ...]

┌──────────────────┬──────────────┬──────────┬───────────────┐
│ Name             │ Server       │ Status   │ Override Name │
├──────────────────┼──────────────┼──────────┼───────────────┤
│ create_issue     │ github-mcp   │ ACTIVE   │               │
│ search_repos     │ github-mcp   │ ACTIVE   │               │
└──────────────────┴──────────────┴──────────┴───────────────┘

Total: 2 tools
```

**List Namespace Tools**

```bash
$ metamcp-cli namespace:tools --uuid "ns-abc123-..."

┌──────────────────────────────────────┬──────────────┬──────────────┬──────────┬──────────┐
│ UUID                                 │ Name         │ Server       │ Status   │ Override │
├──────────────────────────────────────┼──────────────┼──────────────┼──────────┼──────────┤
│ tool-abc123-...                      │ create_issue │ github-mcp   │ ACTIVE   │          │
└──────────────────────────────────────┴──────────────┴──────────────┴──────────┴──────────┘

Total: 1 tools
```

**Update Tool Status**

```bash
$ metamcp-cli namespace:update-tool-status \
  --namespace-uuid "ns-abc123-..." \
  --tool-uuid "tool-abc123-..." \
  --server-uuid "server-abc123-..." \
  --status "INACTIVE"

✓ Tool status updated to INACTIVE
```

**Update Server Status in Namespace**

```bash
$ metamcp-cli namespace:update-server-status \
  --namespace-uuid "ns-abc123-..." \
  --server-uuid "server-abc123-..." \
  --status "ACTIVE"

✓ Server status updated to ACTIVE
```

---

## Workflows

### Workflow 1: Deploy Template-Based Config

**Goal:** Build and deploy MCP servers from templates to Claude Code.

```bash
# 1. Edit your template config
vim ~/.config/nix/config/claude/mcp.json

# 2. Preview what will be built
uv run buildmcp --dry-run --verbose

# 3. Deploy to Claude Code
uv run buildmcp

# 4. Restart Claude Code to load new config
# (Follow Claude Code restart instructions)
```

### Workflow 2: Import Existing Config to MetaMCP

**Goal:** Import your existing Claude Code config into MetaMCP.

```bash
# 1. Extract mcpServers from Claude config
cat ~/.claude/mcp.json | jq '.mcpServers' > servers.json

# 2. Import to MetaMCP
metamcp-cli server:bulk-import -f servers.json

# 3. Verify import
metamcp-cli server:list

# 4. Browse in TUI
uv run metamcp
```

### Workflow 3: Manage Namespace Tools Interactively

**Goal:** Enable/disable specific tools in a namespace.

```bash
# 1. Launch TUI
uv run metamcp

# 2. Navigate to Namespaces tab

# 3. Select namespace and press Enter

# 4. Navigate to Tools tab

# 5. Select tool and press 't' to toggle status

# 6. Verify changes with CLI
metamcp-cli namespace:tools --uuid "ns-abc123-..."
```

### Workflow 4: Automated Server Provisioning

**Goal:** Script server creation from external source.

```bash
#!/bin/bash
# provision-servers.sh

# Read server list
for server in $(cat servers.txt); do
  # Generate config
  cat > /tmp/server.json <<EOF
{
  "name": "$server",
  "type": "STDIO",
  "command": "npx",
  "args": ["-y", "@scope/$server"]
}
EOF

  # Create server
  metamcp-cli server:create -f /tmp/server.json

  echo "✓ Created $server"
done

echo "Done! Created $(cat servers.txt | wc -l) servers"
```

### Workflow 5: Environment-Specific Deployments

**Goal:** Deploy different configs to dev/staging/prod.

```bash
# Build dev config
uv run buildmcp --mcp-json ~/.config/mcp-dev.json

# Build staging config
uv run buildmcp --mcp-json ~/.config/mcp-staging.json

# Build production config (with force)
uv run buildmcp --mcp-json ~/.config/mcp-prod.json --force
```

### Workflow 6: Backup and Restore

**Goal:** Backup current servers and restore later.

```bash
# Backup
metamcp-cli server:list --format json > backup-$(date +%Y%m%d).json

# Restore
cat backup-20250103.json | \
  jq '{mcpServers: map({(.name): .}) | add}' | \
  metamcp-cli server:bulk-import --stdin
```

### Workflow 7: Cross-Tool Integration

**Goal:** Use all three tools together.

```bash
# 1. Build config with buildmcp
uv run buildmcp --dry-run > preview.txt
cat preview.txt

# 2. Deploy template to file
uv run buildmcp

# 3. Import to MetaMCP
cat ~/.claude/mcp.json | \
  jq '.mcpServers' | \
  metamcp-cli server:bulk-import --stdin

# 4. Verify in TUI
uv run metamcp

# 5. Fine-tune with CLI
metamcp-cli namespace:update-server-status \
  --namespace-uuid "..." \
  --server-uuid "..." \
  --status "ACTIVE"
```

---

## Troubleshooting

### Authentication Issues

**Problem:** `Error: HTTP Error 401: UNAUTHORIZED`

**Solution:**
```bash
# 1. Verify token is set
echo $METAMCP_SESSION_TOKEN

# 2. If empty, set it
export METAMCP_SESSION_TOKEN="your-token"

# 3. Test connection
metamcp-cli server:list

# 4. If still failing, get new token from browser
# DevTools → Application → Cookies → better-auth.session_token
```

### Connection Issues

**Problem:** Cannot connect to MetaMCP server

**Solution:**
```bash
# 1. Check if server is running
curl http://localhost:12008/api/health

# 2. If not running, start MetaMCP server
# (Follow MetaMCP server installation instructions)

# 3. Use correct URL
uv run metamcp --base-url http://localhost:12008
metamcp-cli --base-url http://localhost:12008 server:list

# 4. Check firewall/network
ping localhost
telnet localhost 12008
```

### JSON Parse Errors

**Problem:** `Error: Invalid JSON`

**Solution:**
```bash
# 1. Validate JSON syntax
cat config.json | jq .

# 2. Check for common issues
# - Missing commas
# - Trailing commas
# - Unquoted keys
# - Single quotes (use double quotes)

# 3. Use jq to format
cat config.json | jq '.' > formatted.json
metamcp-cli server:create -f formatted.json
```

### buildmcp Environment Variables

**Problem:** `Missing environment variable: GITHUB_TOKEN`

**Solution:**
```bash
# 1. Check what's missing
uv run buildmcp --dry-run

# 2. Set the variable
export GITHUB_TOKEN="ghp_..."

# 3. Verify
echo $GITHUB_TOKEN

# 4. Add to shell config for persistence
echo 'export GITHUB_TOKEN="ghp_..."' >> ~/.zshrc

# 5. Or use --no-check-env to skip validation
uv run buildmcp --no-check-env
```

### TUI Display Issues

**Problem:** TUI renders incorrectly

**Solution:**
```bash
# 1. Check terminal size
echo $COLUMNS x $LINES

# 2. Resize terminal (minimum 80x24)

# 3. Check terminal type
echo $TERM

# 4. Try different terminal emulator
# - kitty (recommended)
# - alacritty
# - wezterm

# 5. Update terminal
sudo pacman -S kitty  # Arch
```

### Permission Errors

**Problem:** Cannot write to target file

**Solution:**
```bash
# 1. Check file permissions
ls -l ~/.claude/mcp.json

# 2. Check directory permissions
ls -ld ~/.claude

# 3. Create directory if needed
mkdir -p ~/.claude
chmod 755 ~/.claude

# 4. Use different target
uv run buildmcp --mcp-json ~/mcp.json
```

### Checksum Issues

**Problem:** buildmcp says "unchanged" but you want to write

**Solution:**
```bash
# 1. Force write (skip checksum)
uv run buildmcp --force

# 2. Or delete lock file
rm ~/.config/nix/config/claude/mcp.lock

# 3. Then rebuild
uv run buildmcp
```

### Debug Mode

Enable verbose output for all tools:

```bash
# buildmcp verbose
uv run buildmcp --verbose

# TUI with debug
TEXTUAL_LOG=textual.log uv run metamcp
tail -f textual.log

# CLI with error details
metamcp-cli server:list 2>&1 | tee debug.log
```

---

## Additional Resources

- **Documentation:**
  - [buildmcp README](./README.md)
  - [Meta∞MCP TUI Guide](./docs/metamcp.md)
  - [metamcp-cli Guide](./docs/metamcp-cli.md)
  - [MCP Format Specification](./MCP_FORMAT_SPECIFICATION.md)

- **Examples:**
  - [Conversion Examples](./conversion-examples.json)
  - [HAR Files](./har/) - API request examples

- **Project Files:**
  - [CLAUDE.md](./CLAUDE.md) - Project context for Claude
  - [pyproject.toml](./pyproject.toml) - Package configuration

---

## Quick Reference

### buildmcp Commands

```bash
buildmcp                    # Build and deploy
buildmcp --dry-run          # Preview only
buildmcp --force            # Force write
buildmcp --verbose          # Show details
buildmcp --no-check-env     # Skip env validation
```

### TUI Shortcuts

```
q              Quit
r              Refresh
c              Create
d              Delete
i              Import
Enter          Open details
Esc            Back
s              Toggle server status
t              Toggle tool status
```

### CLI Commands

```bash
# Servers
metamcp-cli server:list
metamcp-cli server:create [options]
metamcp-cli server:delete --uuid UUID
metamcp-cli server:bulk-import -f FILE

# Namespaces
metamcp-cli namespace:list
metamcp-cli namespace:get --uuid UUID
metamcp-cli namespace:tools --uuid UUID
metamcp-cli namespace:update-tool-status [options]
metamcp-cli namespace:update-server-status [options]
```

---

**Version:** 0.1.0
**Last Updated:** 2025-01-03
**License:** See LICENSE file
