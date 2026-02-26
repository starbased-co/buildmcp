"""Output format transformers for MCP configurations."""

from abc import ABC, abstractmethod
from typing import Any


class OutputFormatter(ABC):
    """Base class for output format transformers."""

    @property
    @abstractmethod
    def root_key(self) -> str:
        """Root key for the output JSON."""
        ...

    @abstractmethod
    def transform_server(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Transform a single server configuration."""
        ...

    def format(self, servers: dict[str, Any]) -> dict[str, Any]:
        """Format servers dict for output."""
        return {
            self.root_key: {
                name: self.transform_server(name, cfg) for name, cfg in servers.items()
            }
        }


class ClaudeFormatter(OutputFormatter):
    """Claude Code MCP format (default)."""

    CRUSH_FIELDS = {"type", "disabled", "disabled_tools", "timeout", "headers"}

    @property
    def root_key(self) -> str:
        return "mcpServers"

    def transform_server(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        del name  # unused in Claude format
        return {k: v for k, v in config.items() if k not in self.CRUSH_FIELDS}


class CrushFormatter(OutputFormatter):
    """Crush MCP format (charmbracelet/crush)."""

    @property
    def root_key(self) -> str:
        return "mcp"

    def transform_server(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        del name  # unused in Crush format
        result = dict(config)
        result.setdefault("type", "stdio")
        return result


FORMATTERS: dict[str, type[OutputFormatter]] = {
    "claude": ClaudeFormatter,
    "crush": CrushFormatter,
}


def get_formatter(format_type: str) -> OutputFormatter:
    """Get formatter instance by type name."""
    if format_type not in FORMATTERS:
        available = ", ".join(FORMATTERS.keys())
        raise ValueError(f"Unknown format type: {format_type}. Available: {available}")
    return FORMATTERS[format_type]()
