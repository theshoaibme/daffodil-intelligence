"""MCP builder API — parse, validate, probe, and inspect MCP integrations."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..core.security import decode_token
from ..mcp.builder import McpBuilder, McpProbe, get_local_tool_catalog, mcp_sdk_available
from ..mcp.protocol import McpServerSpec, McpServerTestResult, McpStatusDetail, McpValidationResult
from ..mcp.user_store import get_user_server_entries, set_user_server_entries

router = APIRouter(prefix="/mcp", tags=["mcp"])
security = HTTPBearer(auto_error=False)


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


class UserMcpServerEntry(BaseModel):
    name: str
    command: str


class UserMcpServersRequest(BaseModel):
    servers: list[UserMcpServerEntry] = Field(default_factory=list)


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    if not credentials:
        return 0
    try:
        payload = decode_token(credentials.credentials)
        return int(payload.get("sub") or payload.get("user_id") or 0)
    except HTTPException:
        return 0


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


@router.get("/user-servers")
async def mcp_get_user_servers(user_id: int = Depends(get_optional_user_id)):
    """MCP servers saved from the web UI for this user/session."""
    entries = get_user_server_entries(user_id)
    return {"count": len(entries), "servers": entries}


@router.put("/user-servers")
async def mcp_put_user_servers(
    body: UserMcpServersRequest,
    user_id: int = Depends(get_optional_user_id),
):
    """Replace saved MCP servers for this user/session."""
    saved = set_user_server_entries(
        user_id,
        [entry.model_dump() for entry in body.servers],
    )
    return {"count": len(saved), "servers": saved}
