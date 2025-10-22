"""Build and deploy MCP server configurations from templates to their respective targets."""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import attrs
import pyjson5 as json5
import tyro
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from buildmcp.checksum import hash_json_data, write_json_path

console = Console(stderr=True)
err_console = Console(stderr=True)


@attrs.define
class MCPBuilder:
    """Manages building and deploying MCP configurations from templates."""

    mcp_json: Path = Path.home() / ".claude/mcp.json5"
    """Path to the MCP configuration file (JSON5 format)"""

    verbose: bool = False
    """Enable verbose output"""

    dry_run: bool = False
    """Show what would be done without executing"""

    check_env: bool = True
    """Check for missing environment variables"""

    force: bool = False
    """Force write even if checksums match"""

    profile: str | None = None
    """Print built config for specified profile to stdout instead of writing"""

    _missing_vars: set = attrs.field(factory=set, init=False)
    """Track missing environment variables"""

    _profile_hashes: dict[str, str] = attrs.field(factory=dict, init=False)
    """Track built profile hashes for lock file"""

    _locked_hashes: dict[str, str] = attrs.field(factory=dict, init=False)
    """Hashes from lock file"""

    def load_config(self) -> dict[str, Any]:
        """Load the MCP configuration from JSON5 file."""
        if not self.mcp_json.exists():
            err_console.print(
                f"[red]Error:[/red] Configuration file not found: {self.mcp_json}"
            )
            raise SystemExit(1)

        try:
            content = self.mcp_json.read_text()
            return json5.loads(content)
        except (json5.Json5Exception, ValueError) as e:
            err_console.print(f"[red]Error parsing JSON5:[/red] {e}")
            raise SystemExit(1)

    def substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in the form ${VAR_NAME}."""
        if isinstance(data, str):
            # Find all ${VAR_NAME} patterns
            pattern = re.compile(r"\$\{([^}]+)\}")

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
                        for key in ["KEY", "TOKEN", "SECRET", "PASSWORD"]
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
            console.print(
                f"  [dim]Starting with {len(base_servers)} base server(s)[/dim]"
            )

        # Add template servers (overriding base if name conflicts)
        for name in server_names:
            if name not in templates:
                err_console.print(
                    f"[yellow]Warning:[/yellow] Template '{name}' not found"
                )
                continue

            # Clone the template configuration (deep copy to avoid mutation)
            servers[name] = copy.deepcopy(templates[name])

            if self.verbose:
                console.print(f"  [cyan]Added server:[/cyan] {name}")

        return servers

    def load_lock_file(self) -> None:
        """Load profile hashes from lock file."""
        lock_path = self.mcp_json.with_suffix(".lock")
        if lock_path.exists():
            try:
                self._locked_hashes = json.loads(lock_path.read_text())
                if self.verbose:
                    console.print(f"[dim]Loaded lock file: {lock_path}[/dim]")
            except Exception as e:
                if self.verbose:
                    console.print(f"[yellow]Warning:[/yellow] Could not read lock file: {e}")

    def save_lock_file(self) -> None:
        """Save profile hashes to lock file."""
        if not self._profile_hashes:
            return

        lock_path = self.mcp_json.with_suffix(".lock")
        try:
            lock_path.write_text(json.dumps(self._profile_hashes, indent=2) + "\n")
            if self.verbose:
                console.print(f"[dim]Updated lock file: {lock_path}[/dim]")
        except Exception as e:
            err_console.print(f"[yellow]Warning:[/yellow] Could not write lock file: {e}")

    def write_target(
        self, target_spec: str | dict[str, str], servers_json: dict[str, Any]
    ) -> bool:
        """Write configuration to target."""
        json_data = {"mcpServers": servers_json}
        json_str = json.dumps(json_data, indent=2)

        if self.dry_run:
            console.print(f"[yellow]Would write to:[/yellow] {target_spec}")
            console.print(Panel(json_str, title="JSON to write", border_style="yellow"))
            return True

        try:
            if isinstance(target_spec, str) and (
                target_spec.endswith(".json") or target_spec.endswith(".json5")
            ):
                target_path = Path(target_spec).expanduser()
                write_json_path(target_path, servers_json, ".mcpServers")
                console.print(f"  [green]✓[/green] Wrote to {target_path}")
                return True

            elif isinstance(target_spec, dict) and "write" in target_spec:
                write_cmd = target_spec["write"]
                result = subprocess.run(
                    write_cmd,
                    input=json_str,
                    text=True,
                    shell=True,
                    capture_output=True,
                )

                output = (result.stdout or "") + (result.stderr or "")
                success_patterns = [
                    "Configuration saved successfully",
                    "successfully",
                    "Success",
                    "Updated",
                    "Complete",
                ]

                has_success_message = any(
                    pattern.lower() in output.lower() for pattern in success_patterns
                )

                if result.returncode == 0 or has_success_message:
                    if self.verbose and result.stdout:
                        console.print(f"[dim]Output:[/dim] {result.stdout}")
                    if result.stderr and has_success_message:
                        console.print(f"  [green]✓[/green] {result.stderr.strip()}")
                    return True
                else:
                    err_console.print(f"[red]Command failed:[/red] {write_cmd}")
                    if result.stderr:
                        err_console.print(f"[red]Error:[/red] {result.stderr}")
                    elif result.stdout:
                        err_console.print(f"[red]Output:[/red] {result.stdout}")
                    return False
            else:
                err_console.print(
                    f"[red]Error:[/red] Invalid target specification: {target_spec}"
                )
                return False

        except Exception as e:
            err_console.print(f"[red]Failed to write target:[/red] {e}")
            return False

    def process_target(
        self,
        profile_name: str,
        server_names: list[str],
        target_spec: str | dict[str, str],
        templates: dict[str, Any],
        base_servers: dict[str, Any] | None = None,
    ) -> bool:
        """Process a single profile/target by building and writing its configuration."""
        console.print(f"\n[bold cyan]Processing profile:[/bold cyan] {profile_name}")

        # Build the servers JSON from base servers and templates
        servers = self.build_servers_json(server_names, templates, base_servers)

        if not servers:
            console.print(
                f"  [yellow]No valid servers for profile {profile_name}[/yellow]"
            )
            return True

        console.print(f"  [green]Built {len(servers)} server(s)[/green]")

        # Substitute environment variables
        if self.verbose:
            console.print("  [cyan]Substituting environment variables...[/cyan]")

        servers = self.substitute_env_vars(servers)

        # Compute hash of built configuration
        built_hash = hash_json_data(servers)
        self._profile_hashes[profile_name] = built_hash

        if self.verbose:
            console.print(f"  [dim]Built config hash: {built_hash[:16]}...[/dim]")

        # Check if we need to write (compare with locked hash)
        should_write = self.force

        if not self.force:
            locked_hash = self._locked_hashes.get(profile_name)
            if locked_hash:
                if locked_hash == built_hash:
                    console.print(
                        f"  [yellow]⊘[/yellow] Skipping (unchanged, use --force to override)"
                    )
                    return True
                else:
                    if self.verbose:
                        console.print(
                            f"  [dim]Lock hash differs: {locked_hash[:16]}...[/dim]"
                        )
                    should_write = True
            else:
                should_write = True

        # Write to target
        if should_write:
            return self.write_target(target_spec, servers)

        return True

    def run(self) -> None:
        """Execute the MCP configuration build and deployment."""
        # Load configuration
        config = self.load_config()

        # Extract configuration sections (new structure)
        base_servers = config.get("mcpServers", {})
        templates = config.get("templates", {})
        profiles = config.get("profiles", {})
        targets = config.get("targets", {})

        # Handle --profile flag: print built config to stdout and exit
        if self.profile:
            if self.profile not in profiles:
                err_console.print(
                    f"[red]Error:[/red] Profile '{self.profile}' not found in configuration"
                )
                raise SystemExit(1)

            server_names = profiles[self.profile]
            servers = self.build_servers_json(server_names, templates, base_servers)

            if not servers:
                err_console.print(
                    f"[yellow]Warning:[/yellow] No valid servers for profile {self.profile}"
                )
                raise SystemExit(1)

            # Substitute environment variables
            servers = self.substitute_env_vars(servers)

            # Print to stdout (not stderr)
            stdout_console = Console()
            output = {"mcpServers": servers}
            stdout_console.print(json.dumps(output, indent=2))
            return

        # Load lock file
        self.load_lock_file()

        if not profiles:
            console.print("[yellow]No profiles defined in configuration[/yellow]")
            return

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
            table.add_row("Profiles", str(len(profiles)))
            table.add_row("Targets", str(len(targets)))
            console.print(table)

        # Process each profile/target
        success_count = 0
        for profile_name, server_names in profiles.items():
            if profile_name not in targets:
                err_console.print(
                    f"[red]Error:[/red] No target defined for profile '{profile_name}'"
                )
                continue

            target_spec = targets[profile_name]

            if self.process_target(
                profile_name, server_names, target_spec, templates, base_servers
            ):
                success_count += 1
            else:
                err_console.print(f"[red]Failed to process profile:[/red] {profile_name}")

        # Summary
        console.print(
            f"\n[green]✓[/green] Processed {success_count}/{len(profiles)} profiles"
        )

        # Save lock file with updated hashes
        if not self.dry_run:
            self.save_lock_file()

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
