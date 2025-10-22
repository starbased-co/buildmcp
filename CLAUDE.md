# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tool that builds and deploys MCP server configurations from templates to various targets (Claude Code, MCPNest, etc.). It manages the transformation and deployment of MCP server configurations with environment variable substitution.

**Configuration Format**: The tool uses JSON5 (`.json5`) for input configuration files, which allows:
- Comments (single-line `//` and multi-line `/* */`)
- Trailing commas in objects and arrays
- Unquoted object keys
- Single-quoted strings
- Multi-line strings

Output files remain standard JSON for compatibility with MCP clients.

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
uv run buildmcp --profile <name>               # Print built config for profile to stdout
```

## Architecture

### Core Components

#### buildmcp

**MCPBuilder** (`builder.py`): Main class orchestrating the build/deploy process
- Loads configuration from `~/.config/nix/config/claude/mcp.json5` (JSON5 format)
- Processes profiles → builds server configs → writes to targets
- Handles environment variable substitution with `${VAR_NAME}` syntax
- Uses checksums to avoid unnecessary writes

**checksum** (`checksum.py`): Provides JSON/JSON5 hashing and lock file utilities
- Generates SHA256 hashes of built configurations
- Maintains `.lock` files to track configuration changes (standard JSON format)
- Supports reading/writing JSON and JSON5 files at specific paths

### Configuration Flow

1. **Source**: `mcp.json5` (JSON5 format) contains:
   - `templates`: Reusable MCP server definitions
   - `profiles`: Named groups of templates to build (formerly `targets`)
   - `targets`: Output destinations for each profile (formerly `pipes`)
   - `mcpServers`: Base servers included in all profiles

2. **Build Process**:
   ```
   JSON5 Config → Parse → Templates + Base Servers → Environment Substitution → Hash → Compare Lock → Write Target (JSON)
   ```

3. **Target Types**:
   - **JSON file path**: Direct write to `.mcpServers` key (e.g., `~/.claude/mcp.json`)
   - **JSON5 file path**: Direct write to `.mcpServers` key (e.g., `~/.claude/mcp.json5`)
   - **Shell commands**: Object with `read` and `write` commands

4. **Checksum Flow**:
   - Load lock file at start (`mcp.lock` next to `mcp.json5`, always JSON format)
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

Example `mcp.json5` (note JSON5 features: comments, trailing commas):

```json5
{
  // Base servers included in all profiles
  mcpServers: {
    "base-server": { command: "..." },
  },

  // Reusable template definitions
  templates: {
    template1: {
      command: "...",
      args: ["..."],
    },
    template2: {
      command: "...",
      env: { KEY: "${ENV_VAR}" }, // Environment variable substitution
    },
  },

  // Named groups of templates
  profiles: {
    default: ["template1", "template2"],
    minimal: ["template1"],
  },

  // Output destinations for each profile
  targets: {
    default: "~/.claude/mcp.json", // Standard JSON output
    minimal: {
      read: "cat ~/.claude/mcp-minimal.json",
      write: "cat > ~/.claude/mcp-minimal.json",
    },
  },
}
```

### Testing Configurations
Always use `--dry-run` first to:
- Verify JSON5 syntax and structure
- Check environment variable substitution
- Preview target writes without executing

Use `--profile <name>` to inspect a specific profile's built configuration:
- Prints the built config to stdout as JSON
- Performs environment variable substitution
- Does not write to any targets or update lock files
- Useful for debugging, piping to other tools, or manual inspection

Use `--force` to override checksum comparison and write anyway.

## Project Structure

```
buildmcp/
├── src/buildmcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── builder.py        # MCPBuilder class
│   └── checksum.py       # Checksum and lock file utilities
├── tests/                # Test suite (pytest)
├── pyproject.toml        # Project metadata and dependencies
└── CLAUDE.md             # This file
```

### Module Organization

- **buildmcp**: Template-based MCP configuration builder and deployer
- **Dependencies**: `attrs`, `tyro`, `rich`, `dpath`, `pyjson5`

### Entry Points

```toml
[project.scripts]
buildmcp = "buildmcp.builder:main"
```

### Notes

- **Tests**: Pytest configured in `pyproject.toml`, test files in `tests/`
- **Configuration**: Config lives in user's nix config directory (`~/.config/nix/config/claude/mcp.json5`)
- **JSON5 Benefits**: Comments allow documentation, trailing commas prevent merge conflicts, unquoted keys improve readability