# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project contains two main tools for working with MCP (Model Context Protocol) servers:

### buildmcp
Python CLI tool that builds and deploys MCP server configurations from templates to various targets (Claude Code, MCPNest, etc.). It manages the transformation and deployment of MCP server configurations with environment variable substitution.

### Meta∞MCP
Terminal User Interface (TUI) for managing MCP servers through the MetaMCP web application API. Provides interactive browsing, creation, deletion, and bulk import of MCP server configurations.

## Development Commands

### Setup
```bash
# Create/activate virtual environment
source .venv/bin/activate  # Automatically activated via .envrc

# Install dependencies
uv add <package>           # Add new dependencies
uv sync                    # Install from pyproject.toml

# Run the tool
uv run python main.py      # Direct execution
uv run buildmcp            # Via package script
```

### Common Operations

#### buildmcp
```bash
# Build and deploy MCP configurations
uv run buildmcp --verbose                      # Show detailed output
uv run buildmcp --dry-run                      # Preview without executing
uv run buildmcp --no-check-env                 # Skip env var validation
uv run buildmcp --force                        # Force write even if unchanged
uv run buildmcp --mcp-json <path>              # Use custom config file
```

#### Meta∞MCP
```bash
# Launch TUI for managing MCP servers
export METAMCP_SESSION_TOKEN="your-token"      # Set session token
uv run metamcp                                 # Launch TUI (localhost:12008)
uv run metamcp --base-url http://host:port     # Connect to remote instance
uv run metamcp --cookie-file ~/.metamcp        # Use cookie file for auth

# Extract session token from browser
# 1. Open DevTools → Application → Cookies
# 2. Copy value of 'better-auth.session_token'
# 3. URL-decode if needed
```

## Architecture

### Core Components

#### buildmcp

**MCPBuilder** (`builder.py`): Main class orchestrating the build/deploy process
- Loads configuration from `~/.config/nix/config/claude/mcp.json`
- Processes profiles → builds server configs → writes to targets
- Handles environment variable substitution with `${VAR_NAME}` syntax
- Uses checksums to avoid unnecessary writes

**checksum** (`checksum.py`): Provides JSON hashing and lock file utilities
- Generates SHA256 hashes of built configurations
- Maintains `.lock` files to track configuration changes
- Supports reading/writing JSON at specific paths

#### Meta∞MCP

**MetaMCPClient** (`metamcp.py`): API client for MetaMCP tRPC endpoints
- Implements 6 core operations: list, create, delete, bulk_import, update_tool_status, update_server_status
- Session-based authentication using better-auth cookies
- Full type hints with `@attrs.define` data models
- HTTP client using `httpx` library
- Namespace operations for managing tool and server status

**MetaMCPApp** (`metamcp_tui.py`): Textual-based TUI application
- Tabbed interface with Servers and Namespaces tabs
- Servers tab: Interactive DataTable for browsing servers
- Namespaces tab: Buttons for tool and server status updates
- Form screens for creating servers, bulk importing, and namespace operations
- Keyboard shortcuts: q (quit), r (refresh), c (create), d (delete), i (import)
- Real-time notifications and error handling

### buildmcp Configuration Flow

1. **Source**: `mcp.json` contains:
   - `templates`: Reusable MCP server definitions
   - `profiles`: Named groups of templates to build (formerly `targets`)
   - `targets`: Output destinations for each profile (formerly `pipes`)
   - `mcpServers`: Base servers included in all profiles

2. **Build Process**:
   ```
   Templates + Base Servers → Environment Substitution → Hash → Compare Lock → Write Target
   ```

3. **Target Types**:
   - **JSON file path**: Direct write to `.mcpServers` key (e.g., `~/.claude/mcp.json`)
   - **Shell commands**: Object with `read` and `write` commands

4. **Checksum Flow**:
   - Load lock file at start (`mcp.lock` next to `mcp.json`)
   - For each profile:
     - Build configuration
     - Compute SHA256 hash of built servers
     - Compare with locked hash
     - Skip write if unchanged (unless `--force`)
   - Save all profile hashes to lock file at end

**Lock File Format** (`mcp.lock`):
```json
{
  "profile1": "8062a8bb353ca7a0ae506f4f75de7e6ffc1c1228641d0a3b736b8ea277958238",
  "profile2": "ab260bbff04a7670f3532ba5c36c35cb1f818196cf99ae4f99dbdc495a0aff47"
}
```

### buildmcp Key Design Patterns

- **Profile Composition**: Profiles combine multiple template servers
- **Environment Variables**: `${VAR_NAME}` replaced at build time
- **Checksum Tracking**: Only write when configuration changes (or `--force`)
- **Lock Files**: `.lock` files store hashes for JSON file targets
- **Format Conversion**: Claude Code format differs from MCPNest format
  - Claude: `"type": "stdio"` at top level
  - MCPNest: `"transport": {"type": "stdio"}` nested
- **Dry Run Support**: Preview all operations before execution
- **Missing Variable Tracking**: Collects and reports all missing env vars

### Meta∞MCP API Flow

```
User Action (TUI)
    ↓
MetaMCPApp.action_*()
    ↓
MetaMCPClient._make_request()
    ↓
HTTP POST/GET (httpx)
    ↓
MetaMCP tRPC API (localhost:12008)
    ↓
Database (PostgreSQL/SQLite)
```

**Supported Operations:**

MCP Servers:
- **List**: `GET /trpc/frontend.mcpServers.list?batch=1&input=%7B%7D`
- **Create**: `POST /trpc/frontend.mcpServers.create?batch=1`
- **Delete**: `POST /trpc/frontend.mcpServers.delete?batch=1`
- **Bulk Import**: `POST /trpc/frontend.mcpServers.bulkImport?batch=1`

Namespaces:
- **Update Tool Status**: `POST /trpc/frontend.namespaces.updateToolStatus?batch=1`
- **Update Server Status**: `POST /trpc/frontend.namespaces.updateServerStatus?batch=1`

**Authentication:** Session token from `better-auth.session_token` cookie
**Data Format:** tRPC batch format with `{"0": {...}}` payload wrapper

## Working with MCP Formats

### Format Differences
- **Claude Code**: Uses top-level `type` field for transport
- **MCPNest**: Requires nested `transport` object
- See `MCP_FORMAT_SPECIFICATION.md` for complete format details
- See `conversion-examples.json` for transformation examples

### Adding New Templates
Templates go in the config file and should include:
- Command and arguments
- Environment variables as `${VAR_NAME}` placeholders
- Appropriate format for target platform

### Configuration Structure Example

```json
{
  "mcpServers": {
    "base-server": { "command": "..." }
  },
  "templates": {
    "template1": { "command": "...", "args": ["..."] },
    "template2": { "command": "...", "env": {"KEY": "${ENV_VAR}"} }
  },
  "profiles": {
    "default": ["template1", "template2"],
    "minimal": ["template1"]
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

### Testing Configurations
Always use `--dry-run` first to:
- Verify JSON structure
- Check environment variable substitution
- Preview target writes without executing

Use `--force` to override checksum comparison and write anyway.

## Project Structure

```
buildmcp/
├── src/buildmcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── builder.py        # MCPBuilder class for buildmcp CLI
│   ├── checksum.py       # Checksum and lock file utilities
│   ├── metamcp.py        # MetaMCP API client
│   └── metamcp_tui.py    # Meta∞MCP TUI application
├── docs/
│   ├── metamcp.md        # Meta∞MCP documentation
│   └── metamcp-deploy.md # Original proof-of-concept docs
├── har/                  # HTTP Archive files for API reference
│   ├── list.har
│   ├── create.har
│   ├── delete.har
│   ├── bulkImport.har
│   ├── namespaces.updateToolStatus.har
│   └── namespaces.updateServerStatus.har
├── tests/                # Test suite (pytest)
├── pyproject.toml        # Project metadata and dependencies
└── CLAUDE.md             # This file

```

### Module Organization

- **buildmcp**: Template-based MCP configuration builder and deployer
- **Meta∞MCP**: Interactive TUI for direct MCP server management via API
- **Shared dependencies**: `attrs`, `tyro`, `rich`, `httpx`
- **TUI framework**: `textual` for Meta∞MCP interface

### Entry Points

```toml
[project.scripts]
buildmcp = "buildmcp.builder:main"    # Configuration builder
metamcp = "buildmcp.metamcp_tui:main" # Meta∞MCP TUI
```

### Notes

- **Tests**: Pytest configured in `pyproject.toml`, test files in `tests/`
- **Configuration**: buildmcp config lives in user's nix config directory
- **HAR files**: Capture real API requests for documentation and testing
- **Documentation**: See `docs/metamcp.md` for complete Meta∞MCP guide