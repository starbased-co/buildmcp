#!/usr/bin/env python3
"""Deploy MCP server configurations to metamcp instance."""

import json
import sys
from pathlib import Path
from typing import Annotated

import httpx
import tyro
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def load_session_token(cookie_file: Path | None = None) -> str:
    """Load session token from cookie file or environment."""
    import os

    # Try environment variable first
    token = os.getenv("METAMCP_SESSION_TOKEN")
    if token:
        return token

    # Try reading from cookie file
    if cookie_file and cookie_file.exists():
        # Simple cookie file format: one line with token value
        return cookie_file.read_text().strip()

    err_console.print(
        "[bold red]Error:[/bold red] Session token not found.\n"
        "Set METAMCP_SESSION_TOKEN environment variable or provide --cookie-file"
    )
    sys.exit(1)


def format_for_metamcp(mcp_servers: dict[str, dict]) -> dict:
    """Format MCP servers dict for metamcp API (tRPC batched format)."""
    return {"0": {"mcpServers": mcp_servers}}


def deploy_to_metamcp(
    mcp_servers: dict[str, dict],
    base_url: str,
    session_token: str,
    timeout: float = 30.0,
) -> dict:
    """Deploy MCP servers to metamcp instance."""
    url = f"{base_url}/trpc/frontend.mcpServers.bulkImport?batch=1"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"better-auth.session_token={session_token}",
    }

    payload = format_for_metamcp(mcp_servers)

    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        err_console.print(f"[bold red]HTTP Error {e.response.status_code}:[/bold red]")
        err_console.print(e.response.text)
        sys.exit(1)
    except httpx.RequestError as e:
        err_console.print(f"[bold red]Request Error:[/bold red] {e}")
        sys.exit(1)


def main(
    input_file: Path,
    /,
    base_url: Annotated[
        str,
        tyro.conf.arg(help="Base URL of metamcp instance"),
    ] = "http://localhost:12008",
    cookie_file: Annotated[
        Path | None,
        tyro.conf.arg(help="File containing session token"),
    ] = None,
    dry_run: Annotated[
        bool,
        tyro.conf.arg(help="Preview payload without sending"),
    ] = False,
    verbose: Annotated[
        bool,
        tyro.conf.arg(help="Show detailed output"),
    ] = False,
) -> None:
    """Deploy MCP server configurations to metamcp instance."""
    # Validate input file
    if not input_file.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {input_file}")
        sys.exit(1)

    # Load MCP servers
    try:
        data = json.loads(input_file.read_text())

        # Extract mcpServers if it's wrapped
        if isinstance(data, dict) and "mcpServers" in data:
            mcp_servers = data["mcpServers"]
        else:
            mcp_servers = data
    except json.JSONDecodeError as e:
        err_console.print(f"[bold red]Invalid JSON:[/bold red] {e}")
        sys.exit(1)

    if not isinstance(mcp_servers, dict):
        err_console.print(
            "[bold red]Error:[/bold red] Input must be a dict of MCP servers"
        )
        sys.exit(1)

    # Display servers table
    table = Table(title="MCP Servers to Deploy", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Details", style="green")

    for name, config in mcp_servers.items():
        server_type = config.get("type", "unknown")
        if server_type == "stdio":
            details = config.get("command", "")
        elif server_type == "http":
            details = config.get("url", "")
        elif server_type == "sse":
            details = config.get("url", "")
        else:
            details = str(config)

        table.add_row(name, server_type, details[:50])

    console.print(table)

    # Dry run mode
    if dry_run:
        payload = format_for_metamcp(mcp_servers)
        console.print("\n[cyan]Payload Preview:[/cyan]")
        console.print(json.dumps(payload, indent=2))
        console.print("\n[yellow]Dry run - no request sent[/yellow]")
        return

    # Load session token
    session_token = load_session_token(cookie_file)

    # Deploy
    console.print(f"\n[cyan]Deploying to:[/cyan] {base_url}")

    result = deploy_to_metamcp(mcp_servers, base_url, session_token)

    # Parse response
    if verbose:
        console.print("\n[cyan]Raw Response:[/cyan]")
        console.print(json.dumps(result, indent=2))

    # Extract result from tRPC batch response
    if isinstance(result, list) and len(result) > 0:
        batch_result = result[0].get("result", {}).get("data", {})

        if batch_result.get("success"):
            console.print(
                Panel(
                    f"[green]✓[/green] {batch_result.get('message', 'Success')}",
                    title="Deployment Success",
                    border_style="green",
                )
            )
        else:
            err_console.print(
                Panel(
                    f"[red]✗[/red] Deployment failed",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    else:
        console.print("[yellow]⚠[/yellow] Unexpected response format")


if __name__ == "__main__":
    tyro.cli(main)
