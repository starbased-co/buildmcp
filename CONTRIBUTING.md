# Contributing to buildmcp

Thank you for your interest in contributing to buildmcp! This guide will help you get started.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

---

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- git
- A MetaMCP server instance (for testing TUI/CLI features)

### Initial Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/buildmcp.git
cd buildmcp

# Install dependencies
uv sync

# Install development dependencies
uv sync --group dev

# Verify installation
uv run buildmcp --help
uv run metamcp --help
uv run metamcp-cli --help
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/buildmcp --cov-report=html

# Run specific test file
uv run pytest tests/test_builder.py

# Run specific test
uv run pytest tests/test_builder.py::test_build_profile

# Run with verbose output
uv run pytest -v
```

---

## Project Structure

```
buildmcp/
├── src/buildmcp/           # Source code
│   ├── builder.py          # buildmcp - Template builder
│   ├── checksum.py         # Checksum and lock file utilities
│   ├── metamcp.py          # MetaMCP API client
│   ├── metamcp_tui.py      # Meta∞MCP TUI application
│   └── metamcp_cli.py      # metamcp-cli command-line tool
├── tests/                  # Test suite
│   ├── test_builder.py     # buildmcp tests
│   ├── test_checksum.py    # Checksum tests
│   └── conftest.py         # pytest fixtures
├── docs/                   # Documentation
│   ├── metamcp.md          # TUI documentation
│   ├── metamcp-cli.md      # CLI documentation
│   └── metamcp-deploy.md   # Deployment guide
├── har/                    # HTTP Archive files (API examples)
├── README.md               # Main readme
├── USAGE.md                # Complete usage guide
├── QUICKSTART.md           # Quick start guide
├── CONTRIBUTING.md         # This file
├── CLAUDE.md               # Project context for Claude
├── pyproject.toml          # Package configuration
└── uv.lock                 # Dependency lock file
```

### Module Overview

- **builder.py** - Template-based configuration builder
  - `MCPBuilder` class
  - Template composition
  - Environment variable substitution
  - Checksum tracking

- **checksum.py** - Utilities for JSON hashing and lock files
  - `hash_json()` - Generate SHA256 checksums
  - `read_lock_file()` / `write_lock_file()`
  - `read_json_at_path()` / `write_json_at_path()`

- **metamcp.py** - MetaMCP API client (shared by TUI and CLI)
  - `MetaMCPClient` - Main client class
  - Data models: `MetaMCPServer`, `Namespace`, `NamespaceTool`
  - API methods: list/create/delete servers, manage namespaces

- **metamcp_tui.py** - Textual-based TUI
  - `MetaMCPApp` - Main application
  - `NamespaceDetailsScreen` - Namespace viewer
  - Create/import screens

- **metamcp_cli.py** - Command-line interface
  - Server commands (list, create, delete, bulk-import)
  - Namespace commands (list, get, tools, update-status)
  - JSON input support (file, stdin, pipe)

---

## Coding Standards

We follow Python best practices and project-specific conventions.

### Python Style

- **Python Version**: 3.12+
- **Style Guide**: PEP 8 with 100 character line limit
- **Type Hints**: Required on all function signatures
- **Docstrings**: Required for public functions and classes

### Code Conventions

From `~/.config/nix/config/claude/standards-python.md`:

```python
# Modern Python 3.12+ syntax
def process(data: str | bytes | None = None) -> dict[str, Any] | None:
    """Process data and return result."""
    ...

# Use attrs for data classes
import attrs

@attrs.define
class Config:
    """Configuration with validation."""
    api_key: str = attrs.field(validator=attrs.validators.instance_of(str))
    timeout: float = 30.0

# Error handling with logging
import logging
logger = logging.getLogger(__name__)

try:
    result = process_data(input_data)
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return None
```

### Naming Conventions

- **Functions/Methods**: `snake_case` (`process_data`, `calculate_total`)
- **Classes**: `PascalCase` (`DataProcessor`, `MCPBuilder`)
- **Constants**: `UPPER_SNAKE_CASE` (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private**: Leading underscore (`_internal_helper`, `_cache`)

### Import Order

```python
# Standard library
import json
import sys
from pathlib import Path
from typing import Annotated

# Third-party
import attrs
import tyro
from rich.console import Console

# Local
from buildmcp.metamcp import get_client
```

### Rich Output

Use Rich for terminal output:

```python
from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

# Tables
table = Table(title="Results")
table.add_column("Name", style="green")
table.add_row("test")
console.print(table)

# Status messages
console.print("[green]✓[/green] Success")
err_console.print("[red]Error:[/red] Failed")
```

---

## Testing

### Test Structure

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test component interactions
- **Fixtures**: Shared test data in `conftest.py`

### Writing Tests

```python
import pytest
from buildmcp.builder import MCPBuilder

def test_build_profile():
    """Test building a profile from templates."""
    builder = MCPBuilder(config_path="test-config.json")
    result = builder.build_profile("default")

    assert result["mcpServers"]["github"]
    assert result["mcpServers"]["github"]["command"] == "npx"

@pytest.fixture
def sample_config():
    """Fixture providing sample configuration."""
    return {
        "templates": {
            "test": {"command": "npx"}
        },
        "profiles": {
            "default": ["test"]
        }
    }

def test_with_fixture(sample_config):
    """Test using fixture."""
    assert "templates" in sample_config
```

### Testing TUI

For TUI testing, use Textual's testing utilities:

```python
from textual.pilot import Pilot
from buildmcp.metamcp_tui import MetaMCPApp

async def test_app():
    """Test TUI application."""
    app = MetaMCPApp(client=mock_client)
    async with app.run_test() as pilot:
        # Simulate key presses
        await pilot.press("r")  # Refresh

        # Check state
        assert len(app.servers) > 0
```

### Running Specific Tests

```bash
# Run tests matching pattern
uv run pytest -k "test_build"

# Run tests in directory
uv run pytest tests/

# Run with markers
uv run pytest -m "slow"

# Stop on first failure
uv run pytest -x
```

---

## Documentation

### Code Documentation

- **Docstrings**: Use Google style
- **Type Hints**: Always include
- **Comments**: Explain WHY, not WHAT

```python
def process_template(
    template: dict[str, Any],
    env_vars: dict[str, str],
) -> dict[str, Any]:
    """Process template with environment variable substitution.

    Args:
        template: Template configuration dictionary
        env_vars: Environment variables for substitution

    Returns:
        Processed template with substituted values

    Raises:
        ValueError: If template is invalid
        KeyError: If required env var is missing
    """
    ...
```

### User Documentation

When adding features, update:

- **README.md** - If it's a major feature
- **USAGE.md** - Add workflow examples
- **Tool-specific docs** - Update relevant doc file
- **QUICKSTART.md** - If it affects getting started

### Commit Messages

Follow conventional commits:

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Testing
- chore: Maintenance

Examples:
feat(cli): add JSON stdin support
fix(builder): handle missing env vars correctly
docs(tui): add namespace management guide
```

---

## Submitting Changes

### Before Submitting

1. **Run tests**
   ```bash
   uv run pytest
   ```

2. **Format code**
   ```bash
   uv run ruff format .
   ```

3. **Lint code**
   ```bash
   uv run ruff check --fix .
   ```

4. **Type check**
   ```bash
   uv run mypy src/buildmcp
   ```

5. **Update documentation**
   - Add docstrings
   - Update relevant .md files
   - Add examples if needed

### Pull Request Process

1. **Fork the repository**
   ```bash
   # On GitHub, click "Fork"
   git clone https://github.com/YOUR_USERNAME/buildmcp.git
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write code
   - Add tests
   - Update docs

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat(scope): add feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in description

### PR Description Template

```markdown
## Summary
Brief description of changes

## Changes
- Added feature X
- Fixed bug Y
- Updated documentation Z

## Testing
- [ ] All tests pass
- [ ] Added new tests for new features
- [ ] Manually tested TUI/CLI
- [ ] Updated documentation

## Screenshots
(If applicable, especially for TUI changes)

## Related Issues
Closes #123
```

---

## Development Workflows

### Adding a New CLI Command

1. **Add function** to `metamcp_cli.py`:
   ```python
   def server_new_action(
       arg: Annotated[str, tyro.conf.arg(help="Description")],
   ) -> None:
       """New server action."""
       client = get_client()
       # Implementation
       console.print("[green]✓[/green] Done")
   ```

2. **Register in main()**:
   ```python
   tyro.extras.subcommand_cli_from_dict({
       "server:new-action": server_new_action,
       # ... other commands
   })
   ```

3. **Add tests**:
   ```python
   def test_server_new_action():
       """Test new action."""
       # Test implementation
   ```

4. **Update docs**:
   - Add to `docs/metamcp-cli.md`
   - Add example to `USAGE.md`

### Adding a TUI Screen

1. **Create screen class** in `metamcp_tui.py`:
   ```python
   class NewFeatureScreen(Screen):
       """Screen for new feature."""

       BINDINGS = [
           Binding("escape", "cancel", "Cancel"),
       ]

       def compose(self) -> ComposeResult:
           yield Header()
           yield Container(...)
           yield Footer()
   ```

2. **Add navigation** from main app
3. **Test interactively**
4. **Update docs**

### Adding API Method

1. **Add method** to `MetaMCPClient` in `metamcp.py`:
   ```python
   def new_operation(self, param: str) -> Result:
       """New API operation."""
       result = self._make_request("POST", "endpoint", {"param": param})
       # Process result
       return result
   ```

2. **Add data model** if needed:
   ```python
   @attrs.define
   class NewModel:
       """Model for new data."""
       field: str
       value: int
   ```

3. **Use in TUI/CLI**
4. **Add tests**

---

## Code Review Checklist

Before requesting review, ensure:

- [ ] Code follows style guide
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Type hints are present
- [ ] Error handling is appropriate
- [ ] Commit messages follow convention
- [ ] No debug code or print statements
- [ ] Sensitive data is not committed
- [ ] Changes are focused and minimal

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/starbased-co/buildmcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/starbased-co/buildmcp/discussions)
- **Documentation**: See [USAGE.md](./USAGE.md)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to buildmcp!** 🎉
