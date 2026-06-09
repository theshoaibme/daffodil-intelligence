"""MCP builder API — parse, validate, probe, and inspect MCP integrations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..mcp.builder import McpBuilder, McpProbe, get_local_tool_catalog, mcp_sdk_available
from ..mcp.protocol import McpServerSpec, McpServerTestResult, McpStatusDetail, McpValidationResult

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ParseEntryRequest(BaseModel):
    entry: str = Field(..., description="name=command arg1 arg2")


class ValidateServerRequest(BaseModel):
    name: str
    command: str


class TestServerRequest(BaseModel):
    name: str | None = None
    command: str | None = None
    entry: str | None = None
    test_self: bool = False
    timeout_seconds: float = Field(default=20.0, ge=3.0, le=60.0)


@router.get("/status", response_model=McpStatusDetail)
async def mcp_builder_status():
    """Full MCP integration status including parsed server specs."""
    return McpBuilder.status_detail()


@router.get("/catalog")
async def mcp_local_catalog():
    """Tools exposed by Daffodil's own MCP server (from ToolRegistry)."""
    tools = get_local_tool_catalog()
    return {"count": len(tools), "tools": tools}


@router.get("/servers")
async def mcp_configured_servers(include_self: bool = False):
    """Parsed MCP server definitions from environment."""
    specs = McpBuilder.get_configured_specs(include_self=include_self)
    return {
        "count": len(specs),
        "servers": [s.model_dump() for s in specs],
        "serialized": McpBuilder.serialize_specs(specs),
    }


@router.post("/parse")
async def mcp_parse_entry(body: ParseEntryRequest):
    spec = McpBuilder.parse_entry(body.entry)
    if spec is None:
        raise HTTPException(status_code=400, detail="Invalid entry format; use name=command arg1 arg2")
    return {"spec": spec.model_dump(), "validation": McpBuilder.validate(spec).model_dump()}


@router.post("/validate", response_model=McpValidationResult)
async def mcp_validate_server(body: ValidateServerRequest):
    try:
        spec = McpBuilder.from_name_command(body.name, body.command)
    except ValueError as e:
        return McpValidationResult(valid=False, errors=[str(e)])
    return McpBuilder.validate(spec)


@router.post("/test", response_model=McpServerTestResult)
async def mcp_test_server(body: TestServerRequest):
    if not mcp_sdk_available():
        raise HTTPException(status_code=503, detail="MCP SDK not installed")

    if body.test_self:
        return await McpProbe.test_self(timeout_seconds=body.timeout_seconds)

    spec: McpServerSpec | None = None
    if body.entry:
        spec = McpBuilder.parse_entry(body.entry)
    elif body.name and body.command:
        try:
            spec = McpBuilder.from_name_command(body.name, body.command)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    if spec is None:
        raise HTTPException(
            status_code=400,
            detail="Provide test_self=true, entry, or name+command",
        )

    return await McpProbe.test_stdio(spec, timeout_seconds=body.timeout_seconds)
