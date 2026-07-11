# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Cross-Project Documentation — first-party stack

This project is part of Kyle's first-party stack (`~/dev/projects/*`). Sibling projects' curated
documentation does NOT auto-load into your context — you must go read it.

- Before working with or against a first-party dependency's API or behavior, read that project's
  `~/dev/projects/<dep>/AGENTS.md` and `~/dev/projects/<dep>/docs/` directly.
- First-party dependencies of this project: none currently — this section still applies when one is added.
- Answer how/why questions from those curated docs first; sibling source is for verifying or
  extending what the docs say — and it is first-party, editable at the source when work here
  surfaces a problem there.

## Project Overview

Python CLI tool that builds and deploys MCP server configurations from templates to various targets (Claude Code, MCPNest, etc.). It manages the transformation and deployment of MCP server configurations with environment variable substitution.

**Configuration Format**: Uses JSON5 (`.json5`) for input, standard JSON for output. JSON5 allows comments, trailing commas, and unquoted keys.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run buildmcp                    # Build and deploy all profiles
uv run buildmcp --dry-run          # Preview without writing
uv run buildmcp --verbose          # Show detailed output
uv run buildmcp --profile <name>   # Print built config for profile to stdout
uv run buildmcp --force            # Force write (skip checksum comparison)
uv run buildmcp --no-check-env     # Skip env var validation
uv run buildmcp --mcp-json <path>  # Use custom config file

# Run tests
uv run pytest                          # All tests
uv run pytest tests/test_builder.py    # Single file
uv run pytest -k "test_name"           # Single test by name
uv run pytest -x                       # Stop on first failure
```

## Architecture

### Core Components

**MCPBuilder** (`src/buildmcp/builder.py`): Main orchestrator class
- Loads configuration from `~/.claude/mcp.json5`
- Processes profiles → builds server configs → writes to targets
- Handles `${VAR_NAME}` environment variable substitution
- Uses SHA-256 checksums to avoid unnecessary writes

**Checksum utilities** (`src/buildmcp/checksum.py`):
- `hash_json_data()`: Generates SHA-256 hashes of built configurations
- `read_json_path()` / `write_json_path()`: Read/write JSON with jq-style path access
- Lock file operations for tracking configuration changes

### Configuration Flow

```
mcp.json5 (JSON5) → Parse → Templates + Base Servers → Env Substitution → Hash → Compare Lock → Write Target (JSON)
```

### Configuration Structure

```json5
{
  mcpServers: { /* Base servers included in all profiles */ },
  templates: {
    "template-name": {
      name: "custom-output-key",  // Optional: custom key in output
      command: "...",
      env: { KEY: "${ENV_VAR}" },
    },
  },
  profiles: {
    default: ["template1", "template2"],  // Template names to include
  },
  targets: {
    default: "~/.claude/mcp.json",        // JSON file path
    // Or shell command:
    custom: { read: "cmd", write: "cmd" },
  },
}
```

### Target Types

- **JSON/JSON5 file path**: Direct write to `.mcpServers` key
- **Shell commands**: Object with `read` and `write` commands (for tools like mcpnest-cli)

### Lock File

`mcp.lock` (JSON) stores profile name → hash mappings. Profiles are skipped if hash matches unless `--force` is used.
