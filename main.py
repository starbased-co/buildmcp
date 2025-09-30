#!/usr/bin/env python3
"""Build and deploy MCP server configurations from templates to their respective pipes."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import attrs
import tyro
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(stderr=True)
err_console = Console(stderr=True)


@attrs.define
class MCPBuilder:
    """Manages building and deploying MCP configurations from templates."""

    config_path: Path = Path.home() / ".config/nix/config/claude/mcp.json"
    """Path to the MCP configuration file"""

    verbose: bool = False
    """Enable verbose output"""

    dry_run: bool = False
    """Show what would be done without executing"""

    check_env: bool = True
    """Check for missing environment variables"""

    _missing_vars: set = attrs.field(factory=set, init=False)
    """Track missing environment variables"""

    def load_config(self) -> dict[str, Any]:
        """Load the MCP configuration from file."""
        if not self.config_path.exists():
            err_console.print(f"[red]Error:[/red] Configuration file not found: {self.config_path}")
            raise tyro.cli.Exit(code=1)

        try:
            with self.config_path.open() as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Error parsing JSON:[/red] {e}")
            raise tyro.cli.Exit(code=1)

    def substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in the form ${VAR_NAME}."""
        if isinstance(data, str):
            # Find all ${VAR_NAME} patterns
            pattern = re.compile(r'\$\{([^}]+)\}')

            def replace_var(match):
                var_name = match.group(1)
                value = os.getenv(var_name)

                if value is None:
                    self._missing_vars.add(var_name)
                    if self.check_env and self.verbose:
                        err_console.print(
                            f"    [yellow]Missing:[/yellow] Environment variable '{var_name}' not set"
                        )
                    # Return the original placeholder if not found
                    return match.group(0)

                if self.verbose:
                    # Show first/last 3 chars for sensitive data
                    if len(value) > 10 and any(
                        key in var_name.upper()
                        for key in ['KEY', 'TOKEN', 'SECRET', 'PASSWORD']
                    ):
                        display_value = f"{value[:3]}...{value[-3:]}"
                    else:
                        display_value = value
                    console.print(
                        f"    [dim]Substituted ${{{var_name}}} → {display_value}[/dim]"
                    )

                return value

            return pattern.sub(replace_var, data)

        elif isinstance(data, dict):
            return {key: self.substitute_env_vars(value) for key, value in data.items()}

        elif isinstance(data, list):
            return [self.substitute_env_vars(item) for item in data]

        else:
            # Return primitive types as-is
            return data

    def build_servers_json(
        self,
        server_names: list[str],
        templates: dict[str, Any],
        base_servers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build mcpServers JSON from base servers and template servers."""
        import copy

        # Start with base servers from .mcpServers in config
        servers = copy.deepcopy(base_servers) if base_servers else {}

        if base_servers and self.verbose:
            console.print(f"  [dim]Starting with {len(base_servers)} base server(s)[/dim]")

        # Add template servers (overriding base if name conflicts)
        for name in server_names:
            if name not in templates:
                err_console.print(f"[yellow]Warning:[/yellow] Template '{name}' not found")
                continue

            # Clone the template configuration (deep copy to avoid mutation)
            servers[name] = copy.deepcopy(templates[name])

            if self.verbose:
                console.print(f"  [cyan]Added server:[/cyan] {name}")

        return servers

    def execute_pipe(self, pipe_cmd: str, servers_json: dict[str, Any]) -> bool:
        """Execute a pipe command with JSON input."""
        json_str = json.dumps({"mcpServers": servers_json}, indent=2)

        if self.dry_run:
            console.print(f"[yellow]Would pipe to:[/yellow] {pipe_cmd}")
            console.print(Panel(json_str, title="JSON to pipe", border_style="yellow"))
            return True

        try:
            result = subprocess.run(
                pipe_cmd,
                input=json_str,
                text=True,
                shell=True,
                capture_output=True,
            )

            # Check for success indicators in output
            output = (result.stdout or "") + (result.stderr or "")
            success_patterns = [
                "Configuration saved successfully",
                "successfully",
                "Success",
                "Updated",
                "Complete"
            ]

            has_success_message = any(
                pattern.lower() in output.lower()
                for pattern in success_patterns
            )

            # Consider it successful if either:
            # 1. Return code is 0
            # 2. Output contains success message (even with non-zero return code)
            if result.returncode == 0 or has_success_message:
                if self.verbose and result.stdout:
                    console.print(f"[dim]Output:[/dim] {result.stdout}")

                # Show stderr as info if there's a success message
                if result.stderr and has_success_message:
                    console.print(f"  [green]✓[/green] {result.stderr.strip()}")

                return True
            else:
                err_console.print(f"[red]Command failed:[/red] {pipe_cmd}")
                if result.stderr:
                    err_console.print(f"[red]Error:[/red] {result.stderr}")
                elif result.stdout:
                    err_console.print(f"[red]Output:[/red] {result.stdout}")
                return False

        except Exception as e:
            err_console.print(f"[red]Failed to execute pipe:[/red] {e}")
            return False

    def process_target(
        self,
        target_name: str,
        server_names: list[str],
        pipe_cmd: str,
        templates: dict[str, Any],
        base_servers: dict[str, Any] | None = None,
    ) -> bool:
        """Process a single target by building and piping its configuration."""
        console.print(f"\n[bold cyan]Processing target:[/bold cyan] {target_name}")

        # Build the servers JSON from base servers and templates
        servers = self.build_servers_json(server_names, templates, base_servers)

        if not servers:
            console.print(f"  [yellow]No valid servers for target {target_name}[/yellow]")
            return True

        console.print(f"  [green]Built {len(servers)} server(s)[/green]")

        # Substitute environment variables before piping
        if self.verbose:
            console.print("  [cyan]Substituting environment variables...[/cyan]")

        servers = self.substitute_env_vars(servers)

        # Execute the pipe command
        return self.execute_pipe(pipe_cmd, servers)

    def run(self) -> None:
        """Execute the MCP configuration build and deployment."""
        # Load configuration
        config = self.load_config()

        # Extract configuration sections
        base_servers = config.get("mcpServers", {})
        templates = config.get("templates", {})
        targets = config.get("targets", {})
        pipes = config.get("pipes", {})

        if not targets:
            console.print("[yellow]No targets defined in configuration[/yellow]")
            return

        # Display configuration summary
        if self.verbose:
            table = Table(title="MCP Configuration")
            table.add_column("Component", style="cyan")
            table.add_column("Count", style="green")
            table.add_row("Base Servers", str(len(base_servers)))
            table.add_row("Templates", str(len(templates)))
            table.add_row("Targets", str(len(targets)))
            table.add_row("Pipes", str(len(pipes)))
            console.print(table)

        # Process each target
        success_count = 0
        for target_name, server_names in targets.items():
            if target_name not in pipes:
                err_console.print(
                    f"[red]Error:[/red] No pipe defined for target '{target_name}'"
                )
                continue

            pipe_cmd = pipes[target_name]

            # Skip placeholder pipes
            if "<jq command" in pipe_cmd or "reads server config" in pipe_cmd:
                console.print(
                    f"\n[yellow]Skipping target '{target_name}':[/yellow] "
                    "Pipe command appears to be a placeholder"
                )
                continue

            if self.process_target(target_name, server_names, pipe_cmd, templates, base_servers):
                success_count += 1
            else:
                err_console.print(f"[red]Failed to process target:[/red] {target_name}")

        # Summary
        console.print(f"\n[green]✓[/green] Processed {success_count}/{len(targets)} targets")

        # Report missing environment variables
        if self._missing_vars and self.check_env:
            err_console.print("\n[yellow]Missing environment variables:[/yellow]")
            for var_name in sorted(self._missing_vars):
                err_console.print(f"  • ${{{var_name}}}")
            err_console.print(
                "\n[dim]Set these variables or use --no-check-env to suppress warnings[/dim]"
            )


def main() -> None:
    """CLI entry point."""
    builder = tyro.cli(MCPBuilder)
    builder.run()


if __name__ == "__main__":
    main()