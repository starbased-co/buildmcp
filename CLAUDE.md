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
uv run buildmcp --config-path <path>           # Use custom config file

# Development
uv run python main.py --help                   # Show all CLI options
```

## Architecture

### Core Components

**MCPBuilder** (`main.py`): Main class orchestrating the build/deploy process
- Loads configuration from `~/.config/nix/config/claude/mcp.json`
- Processes templates → builds server configs → pipes to destinations
- Handles environment variable substitution with `${VAR_NAME}` syntax

### Configuration Flow

1. **Source**: `mcp.json` contains:
   - `templates`: Reusable MCP server definitions
   - `targets`: Named groups of templates to deploy together
   - `pipes`: Shell commands to deliver JSON to destinations
   - `mcpServers`: Base servers included in all targets

2. **Build Process**:
   ```
   Templates + Base Servers → Environment Substitution → Target JSON → Pipe Command
   ```

3. **Destinations**: Pipes deliver JSON to:
   - Claude Code config: `~/.claude/mcp.json`
   - MCPNest config: via API
   - Project-local configs: `.mcp.json`

### Key Design Patterns

- **Template Composition**: Targets combine multiple template servers
- **Environment Variables**: `${VAR_NAME}` replaced at build time
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

### Testing Configurations
Always use `--dry-run` first to:
- Verify JSON structure
- Check environment variable substitution
- Preview pipe commands

## Project Structure Notes

- **No tests directory yet**: Consider adding pytest tests
- **Single module design**: All logic in `main.py` (could be split if it grows)
- **Configuration external**: MCP config lives in user's nix config directory
- **Schema files**: JSON schemas document Claude Code and MCPNest formats