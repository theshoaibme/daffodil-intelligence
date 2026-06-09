"""
MCP protocol models (Pydantic)
==============================
Typed representations for MCP server specs, probe results, and tool metadata.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class McpTransport(str, Enum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


class McpServerSpec(BaseModel):
    """A single MCP server definition (stdio or streamable-http)."""

    name: str
    command: str = ""
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None
    transport: McpTransport = McpTransport.STDIO
    url: str | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class McpToolInfo(BaseModel):
    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict, serialization_alias="inputSchema")

    model_config = {"populate_by_name": True}


class McpServerTestResult(BaseModel):
    success: bool
    server_name: str
    message: str
    protocol_version: str | None = None
    server_name_reported: str | None = None
    tool_count: int = 0
    tools: list[str] = Field(default_factory=list)
    latency_ms: float = 0
    error: str | None = None


class McpValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    spec: McpServerSpec | None = None


class McpStatusDetail(BaseModel):
    enabled: bool
    sdk_available: bool
    antigravity_available: bool
    configured: bool
    transport: str
    server_count: int
    servers: list[McpServerSpec] = Field(default_factory=list)
    local_tool_count: int = 0
    status: str
