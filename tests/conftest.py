"""Shared pytest fixtures for buildmcp tests."""

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Provide a valid MCP configuration for testing."""
    return {
        "mcpServers": {
            "base-server": {
                "command": "base-command",
                "args": ["base-arg"],
            }
        },
        "templates": {
            "test-server": {
                "command": "test-command",
                "args": ["test-arg"],
                "env": {"API_KEY": "${API_KEY}"},
            },
            "another-server": {
                "command": "another-command",
                "args": [],
            },
        },
        "profiles": {
            "default": ["test-server", "another-server"],
            "minimal": ["test-server"],
        },
        "targets": {
            "default": "~/.claude/mcp.json",
            "minimal": {
                "read": "cat ~/.claude/mcp-minimal.json",
                "write": "cat > ~/.claude/mcp-minimal.json",
            },
        },
    }


@pytest.fixture
def sample_templates() -> dict[str, Any]:
    """Provide sample template definitions."""
    return {
        "server1": {
            "command": "cmd1",
            "args": ["arg1"],
        },
        "server2": {
            "command": "cmd2",
            "args": ["arg2"],
            "env": {"VAR": "${ENV_VAR}"},
        },
    }


@pytest.fixture
def mock_env(monkeypatch):
    """Provide a fixture to mock environment variables."""

    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)

    return _set_env


@pytest.fixture
def config_file(tmp_path: Path, sample_config: dict[str, Any]) -> Path:
    """Create a temporary config file with sample configuration."""
    config_path = tmp_path / "mcp.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


@pytest.fixture
def empty_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file with minimal valid structure."""
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {},
                "templates": {},
                "profiles": {},
                "targets": {},
            },
            indent=2,
        )
    )
    return config_path
