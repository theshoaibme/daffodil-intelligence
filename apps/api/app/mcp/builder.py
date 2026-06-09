"""
MCP Builder
===========
Central module for parsing, validating, building, and probing MCP servers.

Uses the official ``mcp`` Python SDK (FastMCP server + stdio ClientSession probe)
and ``google.antigravity.types.McpStdioServer`` for agent runtime wiring.
"""

from __future__ import annotations

import logging
import shlex
import sys
import time
from typing import Any

from ..core.config import get_settings
from .protocol import (
    McpServerSpec,
    McpServerTestResult,
    McpStatusDetail,
    McpToolInfo,
    McpTransport,
    McpValidationResult,
)

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    _MCP_SDK = True
except ImportError:  # pragma: no cover
    ClientSession = None  # type: ignore
    StdioServerParameters = None  # type: ignore
    stdio_client = None  # type: ignore
    _MCP_SDK = False

try:
    from google.antigravity.types import McpStdioServer

    _ANTIGRAVITY_MCP = True
except Exception:  # pragma: no cover
    McpStdioServer = None  # type: ignore
    _ANTIGRAVITY_MCP = False


def mcp_sdk_available() -> bool:
    return _MCP_SDK


def antigravity_mcp_available() -> bool:
    return _ANTIGRAVITY_MCP


def get_local_tool_catalog() -> list[dict[str, Any]]:
    """Return the live ToolRegistry manifest (same tools the MCP server exposes)."""
    from ..tools.registry import get_registry

    return get_registry().list_all()


class McpBuilder:
    """Parse, validate, and materialize MCP server configurations."""

    ENTRY_SEP = ","

    @staticmethod
    def parse_command_line(command_line: str) -> tuple[str, list[str]]:
        parts = shlex.split(command_line.strip())
        if not parts:
            raise ValueError("command is empty")
        return parts[0], parts[1:]

    @classmethod
    def parse_entry(cls, entry: str) -> McpServerSpec | None:
        """Parse ``name=command arg1 arg2`` into a spec."""
        entry = entry.strip()
        if not entry or "=" not in entry:
            return None
        name, command_line = entry.split("=", 1)
        name = name.strip()
        command_line = command_line.strip()
        if not name or not command_line:
            return None
        command, args = cls.parse_command_line(command_line)
        return McpServerSpec(name=name, command=command, args=args)

    @classmethod
    def from_name_command(cls, name: str, command: str) -> McpServerSpec:
        command, args = cls.parse_command_line(command)
        return McpServerSpec(name=name.strip(), command=command, args=args)

    @classmethod
    def parse_external_spec(cls, spec: str) -> list[McpServerSpec]:
        if not spec.strip():
            return []
        servers: list[McpServerSpec] = []
        for entry in spec.split(cls.ENTRY_SEP):
            parsed = cls.parse_entry(entry)
            if parsed is not None:
                servers.append(parsed)
        return servers

    @staticmethod
    def serialize_specs(specs: list[McpServerSpec]) -> str:
        parts: list[str] = []
        for spec in specs:
            if spec.transport != McpTransport.STDIO:
                continue
            cmd = " ".join(shlex.quote(p) for p in [spec.command, *spec.args])
            parts.append(f"{spec.name}={cmd}")
        return f"{McpBuilder.ENTRY_SEP} ".join(parts)

    @staticmethod
    def validate(spec: McpServerSpec) -> McpValidationResult:
        errors: list[str] = []
        if not spec.name:
            errors.append("name is required")
        if spec.transport == McpTransport.STDIO and not spec.command:
            errors.append("command is required for stdio transport")
        if spec.transport == McpTransport.STREAMABLE_HTTP and not spec.url:
            errors.append("url is required for streamable-http transport")
        return McpValidationResult(valid=len(errors) == 0, errors=errors, spec=spec)

    @staticmethod
    def to_stdio_parameters(spec: McpServerSpec) -> Any:
        if not _MCP_SDK:
            raise RuntimeError("MCP SDK not installed")
        return StdioServerParameters(
            command=spec.command,
            args=spec.args,
            env=spec.env,
            cwd=spec.cwd,
        )

    @staticmethod
    def to_antigravity_server(spec: McpServerSpec) -> Any | None:
        if not _ANTIGRAVITY_MCP or spec.transport != McpTransport.STDIO:
            return None
        try:
            return McpStdioServer(name=spec.name, command=spec.command, args=spec.args)
        except Exception as e:
            logger.warning("Could not build Antigravity MCP server '%s': %s", spec.name, e)
            return None

    @staticmethod
    def daffodil_self_spec() -> McpServerSpec:
        return McpServerSpec(
            name="daffodil",
            command=sys.executable,
            args=["-m", "app.mcp.server", "stdio"],
        )

    @classmethod
    def get_configured_specs(cls, include_self: bool = False) -> list[McpServerSpec]:
        settings = get_settings()
        if not settings.MCP_ENABLED:
            return []
        specs = cls.parse_external_spec(settings.MCP_EXTERNAL_SERVERS)
        if include_self:
            specs.append(cls.daffodil_self_spec())
        return specs

    @classmethod
    def build_antigravity_servers(cls, include_self: bool = False) -> list[Any]:
        settings = get_settings()
        if not settings.MCP_ENABLED or not _ANTIGRAVITY_MCP:
            return []
        servers: list[Any] = []
        for spec in cls.get_configured_specs(include_self=include_self):
            built = cls.to_antigravity_server(spec)
            if built is not None:
                servers.append(built)
        return servers

    @classmethod
    def status_detail(cls) -> McpStatusDetail:
        settings = get_settings()
        specs = cls.get_configured_specs()
        catalog = get_local_tool_catalog()
        external = (settings.MCP_EXTERNAL_SERVERS or "").strip()
        configured = _MCP_SDK and (len(specs) > 0 or bool(external))

        if not settings.MCP_ENABLED:
            status = "disabled"
        elif not _MCP_SDK:
            status = "sdk_missing"
        elif configured:
            status = "configured"
        else:
            status = "needs_configuration"

        return McpStatusDetail(
            enabled=settings.MCP_ENABLED,
            sdk_available=_MCP_SDK,
            antigravity_available=_ANTIGRAVITY_MCP,
            configured=configured,
            transport=settings.MCP_TRANSPORT,
            server_count=len(specs),
            servers=specs,
            local_tool_count=len(catalog),
            status=status,
        )


class McpProbe:
    """Live connectivity tests against stdio MCP servers via the official client."""

    @staticmethod
    async def test_stdio(
        spec: McpServerSpec,
        timeout_seconds: float = 20.0,
        max_tools: int = 50,
    ) -> McpServerTestResult:
        if not _MCP_SDK:
            return McpServerTestResult(
                success=False,
                server_name=spec.name,
                message="MCP SDK not installed",
                error="pip install mcp",
            )

        validation = McpBuilder.validate(spec)
        if not validation.valid:
            return McpServerTestResult(
                success=False,
                server_name=spec.name,
                message="Invalid server spec",
                error="; ".join(validation.errors),
            )

        start = time.perf_counter()
        params = McpBuilder.to_stdio_parameters(spec)

        try:
            import anyio

            async def _run() -> McpServerTestResult:
                async with stdio_client(params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        init = await session.initialize()
                        tools_result = await session.list_tools()
                        tool_names = [t.name for t in tools_result.tools]
                        server_info = init.serverInfo
                        return McpServerTestResult(
                            success=True,
                            server_name=spec.name,
                            message="Connected and listed tools",
                            protocol_version=init.protocolVersion,
                            server_name_reported=getattr(server_info, "name", None),
                            tool_count=len(tool_names),
                            tools=tool_names[:max_tools],
                            latency_ms=(time.perf_counter() - start) * 1000,
                        )

            with anyio.fail_after(timeout_seconds):
                return await _run()
        except Exception as e:
            return McpServerTestResult(
                success=False,
                server_name=spec.name,
                message="Connection failed",
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )

    @staticmethod
    async def test_self(timeout_seconds: float = 25.0) -> McpServerTestResult:
        return await McpProbe.test_stdio(
            McpBuilder.daffodil_self_spec(),
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    async def list_tools_stdio(
        spec: McpServerSpec,
        timeout_seconds: float = 20.0,
    ) -> list[McpToolInfo]:
        if not _MCP_SDK:
            raise RuntimeError("MCP SDK not installed")

        validation = McpBuilder.validate(spec)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))

        params = McpBuilder.to_stdio_parameters(spec)
        tools: list[McpToolInfo] = []

        import anyio

        async def _run() -> list[McpToolInfo]:
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    for tool in listed.tools:
                        schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
                        tools.append(
                            McpToolInfo(
                                name=tool.name,
                                description=tool.description or "",
                                input_schema=schema or {},
                            )
                        )
                    return tools

        with anyio.fail_after(timeout_seconds):
            return await _run()
