# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`buildmcp` is a Python CLI tool that builds and deploys MCP (Model Context Protocol) server configurations from templates to various targets (Claude Code, MCPNest, etc.). It manages the transformation and deployment of MCP server configurations with environment variable substitution.

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
```bash
# Build and deploy MCP configurations
uv run buildmcp --verbose                      # Show detailed output
uv run buildmcp --dry-run                      # Preview without executing
uv run buildmcp --no-check-env                 # Skip env var validation
uv run buildmcp --force                        # Force write even if unchanged
uv run buildmcp --mcp-json <path>              # Use custom config file

# Development
uv run python main.py --help                   # Show all CLI options
```

## Architecture

### Core Components

**MCPBuilder** (`main.py`): Main class orchestrating the build/deploy process
- Loads configuration from `~/.config/nix/config/claude/mcp.json`
- Processes profiles → builds server configs → writes to targets
- Handles environment variable substitution with `${VAR_NAME}` syntax
- Uses checksums to avoid unnecessary writes

**checksum** (`checksum.py`): Provides JSON hashing and lock file utilities
- Generates SHA256 hashes of built configurations
- Maintains `.lock` files to track configuration changes
- Supports reading/writing JSON at specific paths

### Configuration Flow

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

### Key Design Patterns

- **Profile Composition**: Profiles combine multiple template servers
- **Environment Variables**: `${VAR_NAME}` replaced at build time
- **Checksum Tracking**: Only write when configuration changes (or `--force`)
- **Lock Files**: `.lock` files store hashes for JSON file targets
- **Format Conversion**: Claude Code format differs from MCPNest format
  - Claude: `"type": "stdio"` at top level
  - MCPNest: `"transport": {"type": "stdio"}` nested
- **Dry Run Support**: Preview all operations before execution
- **Missing Variable Tracking**: Collects and reports all missing env vars

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

## Project Structure Notes

- **No tests directory yet**: Consider adding pytest tests
- **Single module design**: All logic in `main.py` (could be split if it grows)
- **Configuration external**: MCP config lives in user's nix config directory
- **Schema files**: JSON schemas document Claude Code and MCPNest formats