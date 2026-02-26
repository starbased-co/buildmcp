"""Tests for output format transformers."""

import pytest

from buildmcp.formatters import (
    ClaudeFormatter,
    CrushFormatter,
    get_formatter,
)


class TestClaudeFormatter:
    """Tests for ClaudeFormatter."""

    def test_claude_formatter_root_key(self):
        """Verify root_key is 'mcpServers'."""
        formatter = ClaudeFormatter()
        assert formatter.root_key == "mcpServers"

    def test_claude_formatter_passthrough(self):
        """Basic config passes through unchanged."""
        formatter = ClaudeFormatter()
        config = {
            "command": "python",
            "args": ["-m", "server"],
            "env": {"API_KEY": "secret"},
        }
        result = formatter.transform_server("test", config)
        assert result == config

    def test_claude_formatter_strips_crush_fields(self):
        """Removes Crush-specific fields: type, disabled, disabled_tools, timeout, headers."""
        formatter = ClaudeFormatter()
        config = {
            "command": "cmd",
            "args": ["arg1"],
            "type": "stdio",
            "disabled": False,
            "disabled_tools": ["tool1"],
            "timeout": 30000,
            "headers": {"Authorization": "Bearer token"},
        }
        result = formatter.transform_server("test", config)
        assert result == {"command": "cmd", "args": ["arg1"]}
        assert "type" not in result
        assert "disabled" not in result
        assert "disabled_tools" not in result
        assert "timeout" not in result
        assert "headers" not in result

    def test_claude_formatter_strips_partial_crush_fields(self):
        """Strips only present Crush fields, preserves others."""
        formatter = ClaudeFormatter()
        config = {
            "command": "node",
            "args": ["server.js"],
            "env": {"DEBUG": "true"},
            "type": "stdio",
            "timeout": 5000,
        }
        result = formatter.transform_server("server", config)
        assert result == {
            "command": "node",
            "args": ["server.js"],
            "env": {"DEBUG": "true"},
        }


class TestCrushFormatter:
    """Tests for CrushFormatter."""

    def test_crush_formatter_root_key(self):
        """Verify root_key is 'mcp'."""
        formatter = CrushFormatter()
        assert formatter.root_key == "mcp"

    def test_crush_formatter_adds_type(self):
        """Adds type: 'stdio' when missing."""
        formatter = CrushFormatter()
        config = {
            "command": "python",
            "args": ["-m", "server"],
        }
        result = formatter.transform_server("test", config)
        assert result["type"] == "stdio"

    def test_crush_formatter_preserves_type(self):
        """Doesn't override existing type field."""
        formatter = CrushFormatter()
        config = {
            "command": "python",
            "args": ["-m", "server"],
            "type": "sse",
        }
        result = formatter.transform_server("test", config)
        assert result["type"] == "sse"

    def test_crush_formatter_preserves_all_fields(self):
        """Keeps all Crush-specific fields intact."""
        formatter = CrushFormatter()
        config = {
            "command": "cmd",
            "args": ["arg1"],
            "type": "stdio",
            "disabled": True,
            "disabled_tools": ["tool1", "tool2"],
            "timeout": 60000,
            "headers": {"X-Custom": "value"},
            "env": {"KEY": "value"},
        }
        result = formatter.transform_server("test", config)
        assert result == config

    def test_crush_formatter_does_not_modify_original(self):
        """Ensure original config dict is not mutated."""
        formatter = CrushFormatter()
        config = {"command": "cmd", "args": []}
        original = dict(config)
        formatter.transform_server("test", config)
        assert config == original


class TestGetFormatter:
    """Tests for get_formatter factory function."""

    def test_get_formatter_claude(self):
        """Returns ClaudeFormatter instance for 'claude'."""
        formatter = get_formatter("claude")
        assert isinstance(formatter, ClaudeFormatter)

    def test_get_formatter_crush(self):
        """Returns CrushFormatter instance for 'crush'."""
        formatter = get_formatter("crush")
        assert isinstance(formatter, CrushFormatter)

    def test_get_formatter_invalid(self):
        """Raises ValueError for unknown format type."""
        with pytest.raises(ValueError, match="Unknown format type: invalid"):
            get_formatter("invalid")

    def test_get_formatter_invalid_lists_available(self):
        """Error message includes available format types."""
        with pytest.raises(ValueError, match="Available: claude, crush"):
            get_formatter("nonexistent")


class TestFormatMethod:
    """Tests for OutputFormatter.format() method."""

    def test_format_multiple_servers_claude(self):
        """Correctly transforms multiple servers for Claude format."""
        formatter = ClaudeFormatter()
        servers = {
            "server1": {"command": "cmd1", "args": [], "type": "stdio"},
            "server2": {"command": "cmd2", "args": ["--flag"], "timeout": 1000},
        }
        result = formatter.format(servers)
        assert result == {
            "mcpServers": {
                "server1": {"command": "cmd1", "args": []},
                "server2": {"command": "cmd2", "args": ["--flag"]},
            }
        }

    def test_format_multiple_servers_crush(self):
        """Correctly transforms multiple servers for Crush format."""
        formatter = CrushFormatter()
        servers = {
            "server1": {"command": "cmd1", "args": []},
            "server2": {"command": "cmd2", "args": ["--flag"], "type": "sse"},
        }
        result = formatter.format(servers)
        assert result == {
            "mcp": {
                "server1": {"command": "cmd1", "args": [], "type": "stdio"},
                "server2": {"command": "cmd2", "args": ["--flag"], "type": "sse"},
            }
        }

    def test_format_empty_servers(self):
        """Handles empty servers dict."""
        formatter = ClaudeFormatter()
        result = formatter.format({})
        assert result == {"mcpServers": {}}

    def test_format_preserves_server_names(self):
        """Server names are preserved in output."""
        formatter = CrushFormatter()
        servers = {
            "my-custom-server": {"command": "cmd"},
            "another_server": {"command": "cmd2"},
        }
        result = formatter.format(servers)
        assert "my-custom-server" in result["mcp"]
        assert "another_server" in result["mcp"]
