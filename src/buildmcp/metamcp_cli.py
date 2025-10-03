#!/usr/bin/env python3
"""Meta∞MCP CLI - Command-line interface for managing MCP servers."""

import dataclasses
import json
import sys
from pathlib import Path
from typing import Annotated

import tyro
from rich.console import Console
from rich.table import Table

from buildmcp.metamcp import get_client

console = Console()
err_console = Console(stderr=True)


def read_json_input(
    file_path: Path | None = None,
    use_stdin: bool = False,
) -> dict:
    """Read JSON from file or stdin."""
    if use_stdin or (not file_path and not sys.stdin.isatty()):
        data = sys.stdin.read()
        return json.loads(data)
    elif file_path:
        return json.loads(file_path.read_text())
    else:
        raise ValueError("No JSON input provided (use -f or pipe to stdin)")


# Server Commands


def server_list() -> None:
    """List all MCP servers."""
    client = get_client()
    servers = client.list_servers()

    table = Table(title="MCP Servers", show_header=True)
    table.add_column("UUID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("URL/Command", style="blue")

    for server in servers:
        details = server.url if server.url else server.command
        table.add_row(
            server.uuid or "",
            server.name,
            server.type,
            details[:60],
        )

    console.print(table)
    console.print(f"\n[green]Total: {len(servers)} servers[/green]")


def server_create(
    name: Annotated[str | None, tyro.conf.arg(help="Server name")] = None,
    server_type: Annotated[
        str | None,
        tyro.conf.arg(help="Server type (STDIO, STREAMABLE_HTTP, SSE)"),
    ] = None,
    description: Annotated[str, tyro.conf.arg(help="Description")] = "",
    command: Annotated[str, tyro.conf.arg(help="Command to execute")] = "",
    url: Annotated[str, tyro.conf.arg(help="Server URL")] = "",
    bearer_token: Annotated[str, tyro.conf.arg(help="Bearer token")] = "",
    file: Annotated[
        Path | None,
        tyro.conf.arg(aliases=["-f"], help="JSON file with server config"),
    ] = None,
    stdin: Annotated[
        bool,
        tyro.conf.arg(help="Read JSON from stdin"),
    ] = False,
) -> None:
    """Create a new MCP server from JSON or CLI args."""
    client = get_client()

    if file or stdin or (not sys.stdin.isatty() and not name):
        data = read_json_input(file, stdin)
        server = client.create_server(
            name=data["name"],
            server_type=data["type"],
            description=data.get("description", ""),
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            url=data.get("url", ""),
            bearer_token=data.get("bearerToken", ""),
        )
    else:
        if not name or not server_type:
            err_console.print(
                "[red]Error: name and server_type are required when not using JSON input[/red]"
            )
            sys.exit(1)

        server = client.create_server(
            name=name,
            server_type=server_type,
            description=description,
            command=command,
            url=url,
            bearer_token=bearer_token,
        )

    console.print(f"[green]✓[/green] Created server: {server.name}")
    console.print(f"  UUID: {server.uuid}")


def server_delete(
    uuid: Annotated[str, tyro.conf.arg(help="Server UUID to delete")],
) -> None:
    """Delete an MCP server."""
    client = get_client()
    client.delete_server(uuid)
    console.print(f"[green]✓[/green] Deleted server: {uuid}")


def server_bulk_import(
    file: Annotated[
        Path | None,
        tyro.conf.arg(aliases=["-f"], help="JSON file with mcpServers config"),
    ] = None,
    stdin: Annotated[
        bool,
        tyro.conf.arg(help="Read JSON from stdin"),
    ] = False,
) -> None:
    """Bulk import MCP servers from JSON (mcpServers format)."""
    client = get_client()
    data = read_json_input(file, stdin)

    if "mcpServers" in data:
        servers = data["mcpServers"]
    else:
        servers = data

    count = client.bulk_import(servers)
    console.print(f"[green]✓[/green] Imported {count} servers")


# Namespace Commands


def namespace_list() -> None:
    """List all namespaces."""
    client = get_client()
    namespaces = client.list_namespaces()

    table = Table(title="Namespaces", show_header=True)
    table.add_column("UUID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="yellow")

    for ns in namespaces:
        table.add_row(
            ns.uuid,
            ns.name,
            ns.description[:60] if ns.description else "",
        )

    console.print(table)
    console.print(f"\n[green]Total: {len(namespaces)} namespaces[/green]")


def namespace_get(
    uuid: Annotated[str, tyro.conf.arg(help="Namespace UUID")],
    show_servers: Annotated[
        bool,
        tyro.conf.arg(help="Show servers table"),
    ] = True,
    show_tools: Annotated[
        bool,
        tyro.conf.arg(help="Show tools table"),
    ] = False,
) -> None:
    """Get namespace details with servers and optionally tools."""
    client = get_client()
    namespace = client.get_namespace(uuid)

    console.print(f"\n[bold cyan]Namespace:[/bold cyan] {namespace.name}")
    console.print(f"[bold]Description:[/bold] {namespace.description}")
    console.print(f"[bold]UUID:[/bold] {namespace.uuid}\n")

    if show_servers:
        servers_table = Table(title="Servers", show_header=True)
        servers_table.add_column("Name", style="green")
        servers_table.add_column("Type", style="yellow")
        servers_table.add_column("Status", style="cyan")
        servers_table.add_column("URL/Command", style="blue")

        for server in namespace.servers:
            details = server.url if server.url else server.command
            servers_table.add_row(
                server.name,
                server.type,
                server.status,
                details[:50],
            )

        console.print(servers_table)

    if show_tools:
        tools = client.get_namespace_tools(uuid)
        tools_table = Table(title="Tools", show_header=True)
        tools_table.add_column("Name", style="green")
        tools_table.add_column("Server", style="yellow")
        tools_table.add_column("Status", style="cyan")
        tools_table.add_column("Override Name", style="blue")

        for tool in tools:
            tools_table.add_row(
                tool.name,
                tool.serverName,
                tool.status,
                tool.overrideName or "",
            )

        console.print(tools_table)
        console.print(f"\n[green]Total: {len(tools)} tools[/green]")


def namespace_tools(
    uuid: Annotated[str, tyro.conf.arg(help="Namespace UUID")],
) -> None:
    """List tools for a namespace."""
    client = get_client()
    tools = client.get_namespace_tools(uuid)

    table = Table(title="Namespace Tools", show_header=True)
    table.add_column("UUID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Server", style="yellow")
    table.add_column("Status", style="cyan")
    table.add_column("Override", style="blue")

    for tool in tools:
        table.add_row(
            tool.uuid,
            tool.name,
            tool.serverName,
            tool.status,
            tool.overrideName or "",
        )

    console.print(table)
    console.print(f"\n[green]Total: {len(tools)} tools[/green]")


def namespace_update_tool_status(
    namespace_uuid: Annotated[str, tyro.conf.arg(help="Namespace UUID")],
    tool_uuid: Annotated[str, tyro.conf.arg(help="Tool UUID")],
    server_uuid: Annotated[str, tyro.conf.arg(help="Server UUID")],
    status: Annotated[
        str,
        tyro.conf.arg(help="Status (ACTIVE or INACTIVE)"),
    ],
) -> None:
    """Update tool status in namespace."""
    if status not in ("ACTIVE", "INACTIVE"):
        err_console.print("[red]Error: status must be ACTIVE or INACTIVE[/red]")
        sys.exit(1)

    client = get_client()
    client.update_tool_status(namespace_uuid, tool_uuid, server_uuid, status)
    console.print(f"[green]✓[/green] Tool status updated to {status}")


def namespace_update_server_status(
    namespace_uuid: Annotated[str, tyro.conf.arg(help="Namespace UUID")],
    server_uuid: Annotated[str, tyro.conf.arg(help="Server UUID")],
    status: Annotated[
        str,
        tyro.conf.arg(help="Status (ACTIVE or INACTIVE)"),
    ],
) -> None:
    """Update server status in namespace."""
    if status not in ("ACTIVE", "INACTIVE"):
        err_console.print("[red]Error: status must be ACTIVE or INACTIVE[/red]")
        sys.exit(1)

    client = get_client()
    client.update_server_status(namespace_uuid, server_uuid, status)
    console.print(f"[green]✓[/green] Server status updated to {status}")


def main() -> None:
    """Entry point for metamcp-cli."""
    try:
        tyro.extras.subcommand_cli_from_dict(
            {
                "server:list": server_list,
                "server:create": server_create,
                "server:delete": server_delete,
                "server:bulk-import": server_bulk_import,
                "namespace:list": namespace_list,
                "namespace:get": namespace_get,
                "namespace:tools": namespace_tools,
                "namespace:update-tool-status": namespace_update_tool_status,
                "namespace:update-server-status": namespace_update_server_status,
            },
            description="Meta∞MCP CLI - Manage MCP servers and namespaces",
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
