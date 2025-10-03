#!/usr/bin/env python3
"""Meta∞MCP TUI - Interactive interface for managing MCP servers."""

import json
from pathlib import Path
from typing import Annotated

import tyro
from rich.table import Table
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from buildmcp.metamcp import (
    MetaMCPClient,
    MetaMCPServer,
    Namespace,
    NamespaceServer,
    NamespaceTool,
    get_client,
)


class CreateServerScreen(Screen):
    """Screen for creating a new MCP server."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Create"),
    ]

    def __init__(self, client: MetaMCPClient) -> None:
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Create New Meta∞MCP Server", id="title"),
            Horizontal(
                Label("Name:", classes="label"),
                Input(placeholder="server-name", id="name"),
            ),
            Horizontal(
                Label("Type:", classes="label"),
                Select(
                    [
                        ("STDIO", "STDIO"),
                        ("STREAMABLE_HTTP", "STREAMABLE_HTTP"),
                        ("SSE", "SSE"),
                    ],
                    id="type",
                ),
            ),
            Horizontal(
                Label("URL:", classes="label"),
                Input(placeholder="https://api.example.com/mcp", id="url"),
            ),
            Horizontal(
                Label("Bearer Token:", classes="label"),
                Input(placeholder="Optional bearer token", id="bearer_token"),
            ),
            Horizontal(
                Label("Command:", classes="label"),
                Input(placeholder="npx", id="command"),
            ),
            Horizontal(
                Label("Args (JSON):", classes="label"),
                Input(placeholder='["-y", "@scope/package"]', id="args"),
            ),
            Horizontal(
                Label("Description:", classes="label"),
                Input(placeholder="Optional description", id="description"),
            ),
            Horizontal(
                Button("Create", variant="success", id="submit"),
                Button("Cancel", variant="default", id="cancel"),
            ),
            id="create-form",
        )
        yield Footer()

    def action_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.app.pop_screen()

    def action_submit(self) -> None:
        """Submit the form."""
        self.query_one("#submit", Button).press()

    @on(Button.Pressed, "#submit")
    def handle_submit(self) -> None:
        """Handle form submission."""
        name = self.query_one("#name", Input).value
        server_type = self.query_one("#type", Select).value
        url = self.query_one("#url", Input).value
        bearer_token = self.query_one("#bearer_token", Input).value
        command = self.query_one("#command", Input).value
        args_str = self.query_one("#args", Input).value
        description = self.query_one("#description", Input).value

        if not name:
            self.notify("Name is required", severity="error")
            return

        if not server_type:
            self.notify("Type is required", severity="error")
            return

        try:
            args = json.loads(args_str) if args_str else []
        except json.JSONDecodeError:
            self.notify("Invalid JSON for args", severity="error")
            return

        try:
            server = self.client.create_server(
                name=name,
                server_type=server_type,
                description=description,
                command=command,
                args=args,
                url=url,
                bearer_token=bearer_token,
            )
            self.notify(f"Created server: {server.name}", severity="information")
            self.app.pop_screen()
        except Exception as e:
            self.notify(f"Error creating server: {e}", severity="error")

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button."""
        self.app.pop_screen()


class UpdateToolStatusScreen(Screen):
    """Screen for updating tool status in namespace."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Update"),
    ]

    def __init__(self, client: MetaMCPClient) -> None:
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Update Tool Status", id="title"),
            Horizontal(
                Label("Namespace UUID:", classes="label"),
                Input(placeholder="d7c51cfb-b7cf-4a1c-be16-4a015bee9438", id="namespace_uuid"),
            ),
            Horizontal(
                Label("Tool UUID:", classes="label"),
                Input(placeholder="6430fda5-5d58-474f-bf5d-0c160c33183c", id="tool_uuid"),
            ),
            Horizontal(
                Label("Server UUID:", classes="label"),
                Input(placeholder="7c3b567f-6e07-4efd-b18c-5a75e0fbecbf", id="server_uuid"),
            ),
            Horizontal(
                Label("Status:", classes="label"),
                Select(
                    [
                        ("ACTIVE", "ACTIVE"),
                        ("INACTIVE", "INACTIVE"),
                    ],
                    id="status",
                ),
            ),
            Horizontal(
                Button("Update", variant="success", id="submit"),
                Button("Cancel", variant="default", id="cancel"),
            ),
            id="create-form",
        )
        yield Footer()

    def action_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.app.pop_screen()

    def action_submit(self) -> None:
        """Submit the form."""
        self.query_one("#submit", Button).press()

    @on(Button.Pressed, "#submit")
    def handle_submit(self) -> None:
        """Handle form submission."""
        namespace_uuid = self.query_one("#namespace_uuid", Input).value
        tool_uuid = self.query_one("#tool_uuid", Input).value
        server_uuid = self.query_one("#server_uuid", Input).value
        status = self.query_one("#status", Select).value

        if not namespace_uuid:
            self.notify("Namespace UUID is required", severity="error")
            return

        if not tool_uuid:
            self.notify("Tool UUID is required", severity="error")
            return

        if not server_uuid:
            self.notify("Server UUID is required", severity="error")
            return

        if not status:
            self.notify("Status is required", severity="error")
            return

        try:
            self.client.update_tool_status(
                namespace_uuid=namespace_uuid,
                tool_uuid=tool_uuid,
                server_uuid=server_uuid,
                status=status,
            )
            self.notify("Tool status updated successfully", severity="information")
            self.app.pop_screen()
        except Exception as e:
            self.notify(f"Error updating tool status: {e}", severity="error")

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button."""
        self.app.pop_screen()


class UpdateServerStatusScreen(Screen):
    """Screen for updating server status in namespace."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Update"),
    ]

    def __init__(self, client: MetaMCPClient) -> None:
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Update Server Status", id="title"),
            Horizontal(
                Label("Namespace UUID:", classes="label"),
                Input(placeholder="d7c51cfb-b7cf-4a1c-be16-4a015bee9438", id="namespace_uuid"),
            ),
            Horizontal(
                Label("Server UUID:", classes="label"),
                Input(placeholder="37c6a033-dc7c-4091-83d7-916d9ef0d7e2", id="server_uuid"),
            ),
            Horizontal(
                Label("Status:", classes="label"),
                Select(
                    [
                        ("ACTIVE", "ACTIVE"),
                        ("INACTIVE", "INACTIVE"),
                    ],
                    id="status",
                ),
            ),
            Horizontal(
                Button("Update", variant="success", id="submit"),
                Button("Cancel", variant="default", id="cancel"),
            ),
            id="create-form",
        )
        yield Footer()

    def action_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.app.pop_screen()

    def action_submit(self) -> None:
        """Submit the form."""
        self.query_one("#submit", Button).press()

    @on(Button.Pressed, "#submit")
    def handle_submit(self) -> None:
        """Handle form submission."""
        namespace_uuid = self.query_one("#namespace_uuid", Input).value
        server_uuid = self.query_one("#server_uuid", Input).value
        status = self.query_one("#status", Select).value

        if not namespace_uuid:
            self.notify("Namespace UUID is required", severity="error")
            return

        if not server_uuid:
            self.notify("Server UUID is required", severity="error")
            return

        if not status:
            self.notify("Status is required", severity="error")
            return

        try:
            self.client.update_server_status(
                namespace_uuid=namespace_uuid,
                server_uuid=server_uuid,
                status=status,
            )
            self.notify("Server status updated successfully", severity="information")
            self.app.pop_screen()
        except Exception as e:
            self.notify(f"Error updating server status: {e}", severity="error")

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button."""
        self.app.pop_screen()


class BulkImportScreen(Screen):
    """Screen for bulk importing servers."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Import"),
    ]

    def __init__(self, client: MetaMCPClient) -> None:
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Bulk Import Meta∞MCP Servers", id="title"),
            Label("Paste JSON configuration (mcpServers format):"),
            TextArea(id="json-input", language="json"),
            Horizontal(
                Button("Import", variant="success", id="submit"),
                Button("Cancel", variant="default", id="cancel"),
            ),
            id="import-form",
        )
        yield Footer()

    def action_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.app.pop_screen()

    def action_submit(self) -> None:
        """Submit the form."""
        self.query_one("#submit", Button).press()

    @on(Button.Pressed, "#submit")
    def handle_submit(self) -> None:
        """Handle form submission."""
        json_str = self.query_one("#json-input", TextArea).text

        if not json_str.strip():
            self.notify("JSON input is required", severity="error")
            return

        try:
            data = json.loads(json_str)
            if "mcpServers" in data:
                servers = data["mcpServers"]
            else:
                servers = data

            count = self.client.bulk_import(servers)
            self.notify(f"Imported {count} servers", severity="information")
            self.app.pop_screen()
        except json.JSONDecodeError as e:
            self.notify(f"Invalid JSON: {e}", severity="error")
        except Exception as e:
            self.notify(f"Error importing servers: {e}", severity="error")

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button."""
        self.app.pop_screen()


class NamespaceDetailsScreen(Screen):
    """Screen showing namespace servers and tools."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "toggle_tool_status", "Toggle Tool Status"),
        Binding("s", "toggle_server_status", "Toggle Server Status"),
    ]

    def __init__(self, client: MetaMCPClient, namespace: Namespace) -> None:
        super().__init__()
        self.client = client
        self.namespace = namespace
        self.tools: list[NamespaceTool] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Namespace: {self.namespace.name}", id="title")
        yield Label(f"Description: {self.namespace.description}", classes="description")
        with TabbedContent(initial="servers-pane"):
            with TabPane("Servers", id="servers-pane"):
                yield DataTable(id="servers-table")
            with TabPane("Tools", id="tools-pane"):
                yield DataTable(id="tools-table")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize tables."""
        servers_table = self.query_one("#servers-table", DataTable)
        servers_table.cursor_type = "row"
        servers_table.add_columns("Name", "Type", "Status", "URL/Command")

        tools_table = self.query_one("#tools-table", DataTable)
        tools_table.cursor_type = "row"
        tools_table.add_columns("Name", "Server", "Status", "Override Name")

        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh namespace data."""
        try:
            namespace = self.client.get_namespace(self.namespace.uuid)
            self.tools = self.client.get_namespace_tools(self.namespace.uuid)

            servers_table = self.query_one("#servers-table", DataTable)
            servers_table.clear()
            for server in namespace.servers:
                details = server.url if server.url else server.command
                servers_table.add_row(
                    server.name,
                    server.type,
                    server.status,
                    details[:40],
                )

            tools_table = self.query_one("#tools-table", DataTable)
            tools_table.clear()
            for tool in self.tools:
                tools_table.add_row(
                    tool.name,
                    tool.serverName,
                    tool.status,
                    tool.overrideName or "",
                )

            self.notify(
                f"Loaded {len(namespace.servers)} servers, {len(self.tools)} tools",
                severity="information",
            )
        except Exception as e:
            self.notify(f"Error refreshing: {e}", severity="error")

    def action_back(self) -> None:
        """Return to main screen."""
        self.app.pop_screen()

    def action_toggle_tool_status(self) -> None:
        """Toggle status of selected tool."""
        tools_table = self.query_one("#tools-table", DataTable)
        row_key = tools_table.cursor_row

        if row_key is None:
            self.notify("No tool selected", severity="warning")
            return

        try:
            tool = self.tools[row_key]
            new_status = "INACTIVE" if tool.status == "ACTIVE" else "ACTIVE"

            self.client.update_tool_status(
                namespace_uuid=self.namespace.uuid,
                tool_uuid=tool.uuid,
                server_uuid=tool.serverUuid,
                status=new_status,
            )

            tool.status = new_status
            tools_table.update_cell(row_key, "Status", new_status)
            self.notify(f"Tool status updated to {new_status}", severity="information")
        except IndexError:
            self.notify("Invalid selection", severity="error")
        except Exception as e:
            self.notify(f"Error updating tool status: {e}", severity="error")

    def action_toggle_server_status(self) -> None:
        """Toggle status of selected server."""
        servers_table = self.query_one("#servers-table", DataTable)
        row_key = servers_table.cursor_row

        if row_key is None:
            self.notify("No server selected", severity="warning")
            return

        try:
            namespace = self.client.get_namespace(self.namespace.uuid)
            server = namespace.servers[row_key]
            new_status = "INACTIVE" if server.status == "ACTIVE" else "ACTIVE"

            self.client.update_server_status(
                namespace_uuid=self.namespace.uuid,
                server_uuid=server.uuid,
                status=new_status,
            )

            servers_table.update_cell(row_key, "Status", new_status)
            self.notify(f"Server status updated to {new_status}", severity="information")
        except IndexError:
            self.notify("Invalid selection", severity="error")
        except Exception as e:
            self.notify(f"Error updating server status: {e}", severity="error")


class MetaMCPApp(App):
    """Meta∞MCP TUI application."""

    TITLE = "Meta∞MCP"

    CSS = """
    #title {
        padding: 1;
        background: $boost;
        color: $text;
        text-align: center;
    }

    .label {
        width: 20;
        padding: 1;
    }

    #create-form {
        width: 80;
        height: auto;
        margin: 2 4;
        padding: 1;
        background: $surface;
    }

    #import-form {
        width: 100;
        height: auto;
        margin: 2 4;
        padding: 1;
        background: $surface;
    }

    #json-input {
        height: 20;
        margin: 1 0;
    }

    Input, Select {
        width: 1fr;
    }

    Horizontal {
        height: auto;
        margin: 0 0 1 0;
    }

    Button {
        margin: 1 1;
    }

    DataTable {
        height: 1fr;
    }

    .description {
        padding: 0 1;
        color: $text-muted;
        margin: 0 0 1 0;
    }

    #details-container {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "create", "Create"),
        Binding("d", "delete", "Delete"),
        Binding("i", "import", "Import"),
    ]

    def __init__(
        self,
        client: MetaMCPClient,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.servers: list[MetaMCPServer] = []
        self.namespaces: list[Namespace] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="servers-tab"):
            with TabPane("Servers", id="servers-tab"):
                yield DataTable(id="servers-table")
            with TabPane("Namespaces", id="namespaces-tab"):
                yield DataTable(id="namespaces-table")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app."""
        servers_table = self.query_one("#servers-table", DataTable)
        servers_table.cursor_type = "row"
        servers_table.add_columns("UUID", "Name", "Type", "URL/Command", "Created")

        namespaces_table = self.query_one("#namespaces-table", DataTable)
        namespaces_table.cursor_type = "row"
        namespaces_table.add_columns("Name", "Description", "Servers", "Created")

        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh server and namespace lists."""
        try:
            self.servers = self.client.list_servers()
            servers_table = self.query_one("#servers-table", DataTable)
            servers_table.clear()

            for server in self.servers:
                details = server.url if server.url else server.command
                servers_table.add_row(
                    server.uuid or "",
                    server.name,
                    server.type,
                    details[:50],
                    server.created_at or "",
                )

            self.namespaces = self.client.list_namespaces()
            namespaces_table = self.query_one("#namespaces-table", DataTable)
            namespaces_table.clear()

            for namespace in self.namespaces:
                full_namespace = self.client.get_namespace(namespace.uuid)
                server_count = len(full_namespace.servers)
                namespaces_table.add_row(
                    namespace.name,
                    namespace.description[:50] if namespace.description else "",
                    str(server_count),
                    namespace.created_at or "",
                )

            self.notify(
                f"Loaded {len(self.servers)} servers, {len(self.namespaces)} namespaces",
                severity="information",
            )
        except Exception as e:
            self.notify(f"Error loading data: {e}", severity="error")

    def action_create(self) -> None:
        """Open create server screen."""
        self.push_screen(CreateServerScreen(self.client))

    def action_delete(self) -> None:
        """Delete selected server."""
        table = self.query_one("#servers-table", DataTable)
        row_key = table.cursor_row

        if row_key is None:
            self.notify("No server selected", severity="warning")
            return

        try:
            server = self.servers[row_key]
            if server.uuid:
                self.client.delete_server(server.uuid)
                self.notify(f"Deleted server: {server.name}", severity="information")
                self.action_refresh()
            else:
                self.notify("Server has no UUID", severity="error")
        except IndexError:
            self.notify("Invalid selection", severity="error")
        except Exception as e:
            self.notify(f"Error deleting server: {e}", severity="error")

    def action_import(self) -> None:
        """Open bulk import screen."""
        self.push_screen(BulkImportScreen(self.client))

    @on(DataTable.RowSelected, "#namespaces-table")
    def handle_namespace_selected(self, event: DataTable.RowSelected) -> None:
        """Open namespace details when row is selected."""
        try:
            namespace = self.namespaces[event.cursor_row]
            full_namespace = self.client.get_namespace(namespace.uuid)
            self.push_screen(NamespaceDetailsScreen(self.client, full_namespace))
        except IndexError:
            self.notify("Invalid selection", severity="error")
        except Exception as e:
            self.notify(f"Error opening namespace: {e}", severity="error")

    def on_screen_resume(self) -> None:
        """Refresh when returning from a screen."""
        self.action_refresh()


def run_tui(
    base_url: Annotated[
        str,
        tyro.conf.arg(help="Base URL of Meta∞MCP instance"),
    ] = "http://localhost:12008",
    cookie_file: Annotated[
        Path | None,
        tyro.conf.arg(help="File containing session token"),
    ] = None,
) -> None:
    """Launch Meta∞MCP TUI for managing MCP servers."""
    import sys

    try:
        client = get_client(base_url=base_url, cookie_file=cookie_file)
        app = MetaMCPApp(client)
        app.run()
    except EnvironmentError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point for metamcp CLI."""
    tyro.cli(run_tui)


if __name__ == "__main__":
    main()
