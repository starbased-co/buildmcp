#!/usr/bin/env python3
"""MetaMCP API client for managing MCP servers."""

import json
import os
import sys
from pathlib import Path
from typing import Any

import attrs
import httpx


@attrs.define
class MetaMCPServer:
    """MCP server configuration."""

    name: str
    type: str
    uuid: str | None = None
    description: str = ""
    command: str = ""
    args: list[str] = attrs.field(factory=list)
    env: dict[str, str] = attrs.field(factory=dict)
    url: str = ""
    bearerToken: str = ""
    created_at: str | None = None
    user_id: str | None = None


@attrs.define
class NamespaceServer:
    """Server within a namespace with status."""

    uuid: str
    name: str
    type: str
    status: str
    description: str = ""
    command: str = ""
    args: list[str] = attrs.field(factory=list)
    env: dict[str, str] = attrs.field(factory=dict)
    url: str = ""
    bearerToken: str = ""
    error_status: str | None = None
    created_at: str | None = None
    user_id: str | None = None


@attrs.define
class NamespaceTool:
    """Tool within a namespace with status and overrides."""

    uuid: str
    name: str
    mcp_server_uuid: str
    serverName: str
    serverUuid: str
    status: str
    description: str = ""
    toolSchema: dict[str, Any] = attrs.field(factory=dict)
    overrideName: str | None = None
    overrideDescription: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@attrs.define
class Namespace:
    """Namespace configuration."""

    uuid: str
    name: str
    description: str = ""
    created_at: str | None = None
    updated_at: str | None = None
    user_id: str | None = None
    servers: list[NamespaceServer] = attrs.field(factory=list)


@attrs.define
class MetaMCPClient:
    """Client for MetaMCP tRPC API."""

    base_url: str
    session_token: str
    timeout: float = 30.0

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with session token."""
        return {
            "Content-Type": "application/json",
            "Cookie": f"better-auth.session_token={self.session_token}",
        }

    def _make_request(
        self, method: str, endpoint: str, payload: dict | None = None
    ) -> dict:
        """Make HTTP request to MetaMCP API."""
        url = f"{self.base_url}/trpc/frontend.mcpServers.{endpoint}"

        try:
            if method == "GET":
                response = httpx.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    follow_redirects=True,
                )
            else:
                response = httpx.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    follow_redirects=True,
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP Error {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Request Error: {e}") from e

    def _make_namespace_request(
        self, method: str, endpoint: str, payload: dict | None = None
    ) -> dict:
        """Make HTTP request to MetaMCP namespaces API."""
        url = f"{self.base_url}/trpc/frontend.namespaces.{endpoint}"

        try:
            if method == "GET":
                response = httpx.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    follow_redirects=True,
                )
            else:
                response = httpx.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    follow_redirects=True,
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP Error {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Request Error: {e}") from e

    def list_servers(self) -> list[MetaMCPServer]:
        """List all MCP servers."""
        result = self._make_request("GET", "list?batch=1&input=%7B%7D")

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to list servers: {data.get('message')}")

        servers = data.get("data", [])
        return [
            MetaMCPServer(
                uuid=s["uuid"],
                name=s["name"],
                description=s.get("description") or "",
                type=s["type"],
                command=s.get("command") or "",
                args=s.get("args", []),
                env=s.get("env", {}),
                url=s.get("url") or "",
                bearerToken=s.get("bearerToken") or "",
                created_at=s.get("created_at"),
                user_id=s.get("user_id"),
            )
            for s in servers
        ]

    def create_server(
        self,
        name: str,
        server_type: str,
        description: str = "",
        command: str = "",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        url: str = "",
        bearer_token: str = "",
    ) -> MetaMCPServer:
        """Create a new MCP server."""
        payload = {
            "0": {
                "name": name,
                "description": description,
                "type": server_type,
                "command": command,
                "args": args or [],
                "env": env or {},
                "url": url,
                "bearerToken": bearer_token,
            }
        }

        result = self._make_request("POST", "create?batch=1", payload)

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to create server: {data.get('message')}")

        server = data["data"]
        return MetaMCPServer(
            uuid=server["uuid"],
            name=server["name"],
            description=server.get("description") or "",
            type=server["type"],
            command=server.get("command") or "",
            args=server.get("args", []),
            env=server.get("env", {}),
            url=server.get("url") or "",
            bearerToken=server.get("bearerToken") or "",
            created_at=server.get("created_at"),
            user_id=server.get("user_id"),
        )

    def delete_server(self, uuid: str) -> bool:
        """Delete an MCP server by UUID."""
        payload = {"0": {"uuid": uuid}}
        result = self._make_request("POST", "delete?batch=1", payload)

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to delete server: {data.get('message')}")

        return True

    def bulk_import(self, servers: dict[str, dict]) -> int:
        """Bulk import MCP servers."""
        payload = {"0": {"mcpServers": servers}}
        result = self._make_request("POST", "bulkImport?batch=1", payload)

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to bulk import: {data.get('message')}")

        return data.get("imported", 0)

    def update_tool_status(
        self,
        namespace_uuid: str,
        tool_uuid: str,
        server_uuid: str,
        status: str,
    ) -> bool:
        """Update tool status in namespace."""
        payload = {
            "0": {
                "namespaceUuid": namespace_uuid,
                "toolUuid": tool_uuid,
                "serverUuid": server_uuid,
                "status": status,
            }
        }
        result = self._make_namespace_request("POST", "updateToolStatus?batch=1", payload)

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to update tool status: {data.get('message')}")

        return True

    def update_server_status(
        self,
        namespace_uuid: str,
        server_uuid: str,
        status: str,
    ) -> bool:
        """Update server status in namespace."""
        payload = {
            "0": {
                "namespaceUuid": namespace_uuid,
                "serverUuid": server_uuid,
                "status": status,
            }
        }
        result = self._make_namespace_request("POST", "updateServerStatus?batch=1", payload)

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to update server status: {data.get('message')}")

        return True

    def list_namespaces(self) -> list[Namespace]:
        """List all namespaces."""
        result = self._make_namespace_request("GET", "list?batch=1&input=%7B%7D")

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to list namespaces: {data.get('message')}")

        namespaces = data.get("data", [])
        return [
            Namespace(
                uuid=ns["uuid"],
                name=ns["name"],
                description=ns.get("description") or "",
                created_at=ns.get("created_at"),
                updated_at=ns.get("updated_at"),
                user_id=ns.get("user_id"),
            )
            for ns in namespaces
        ]

    def get_namespace(self, uuid: str) -> Namespace:
        """Get namespace with servers."""
        import urllib.parse

        query_params = urllib.parse.urlencode({"input": json.dumps({"0": {"uuid": uuid}})})
        result = self._make_namespace_request("GET", f"get?batch=1&{query_params}")

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to get namespace: {data.get('message')}")

        ns = data.get("data")
        if not ns:
            raise RuntimeError("Namespace not found")

        servers = [
            NamespaceServer(
                uuid=s["uuid"],
                name=s["name"],
                type=s["type"],
                status=s["status"],
                description=s.get("description") or "",
                command=s.get("command") or "",
                args=s.get("args", []),
                env=s.get("env", {}),
                url=s.get("url") or "",
                bearerToken=s.get("bearerToken") or "",
                error_status=s.get("error_status"),
                created_at=s.get("created_at"),
                user_id=s.get("user_id"),
            )
            for s in ns.get("servers", [])
        ]

        return Namespace(
            uuid=ns["uuid"],
            name=ns["name"],
            description=ns.get("description") or "",
            created_at=ns.get("created_at"),
            updated_at=ns.get("updated_at"),
            user_id=ns.get("user_id"),
            servers=servers,
        )

    def get_namespace_tools(self, namespace_uuid: str) -> list[NamespaceTool]:
        """Get tools for a namespace."""
        import urllib.parse

        query_params = urllib.parse.urlencode(
            {"input": json.dumps({"0": {"namespaceUuid": namespace_uuid}})}
        )
        result = self._make_namespace_request("GET", f"getTools?batch=1&{query_params}")

        data = result[0]["result"]["data"]
        if not data.get("success"):
            raise RuntimeError(f"Failed to get namespace tools: {data.get('message')}")

        tools = data.get("data", [])
        return [
            NamespaceTool(
                uuid=t["uuid"],
                name=t["name"],
                mcp_server_uuid=t["mcp_server_uuid"],
                serverName=t["serverName"],
                serverUuid=t["serverUuid"],
                status=t["status"],
                description=t.get("description") or "",
                toolSchema=t.get("toolSchema", {}),
                overrideName=t.get("overrideName"),
                overrideDescription=t.get("overrideDescription"),
                created_at=t.get("created_at"),
                updated_at=t.get("updated_at"),
            )
            for t in tools
        ]


def load_session_token(cookie_file: Path | None = None) -> str:
    """Load session token from environment or cookie file."""
    token = os.getenv("METAMCP_SESSION_TOKEN")
    if token:
        return token

    if cookie_file and cookie_file.exists():
        return cookie_file.read_text().strip()

    raise EnvironmentError(
        "Session token not found. "
        "Set METAMCP_SESSION_TOKEN environment variable or provide --cookie-file"
    )


def get_client(
    base_url: str = "http://localhost:12008",
    cookie_file: Path | None = None,
    timeout: float = 30.0,
) -> MetaMCPClient:
    """Get configured MetaMCP client."""
    token = load_session_token(cookie_file)
    return MetaMCPClient(base_url=base_url, session_token=token, timeout=timeout)
