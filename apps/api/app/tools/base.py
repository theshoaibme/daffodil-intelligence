"""
Base Tool Class
===============
All tools in the system inherit from BaseTool.
Provides consistent schema validation and execution contract.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..ui_blocks.schemas import UiBlock
    from .ui_meta import ToolUiMeta


class ToolParameter(BaseModel):
    name: str
    type: str          # 'string', 'integer', 'float', 'boolean', 'list', 'dict'
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    tool_name: str = ""
    duration_ms: float = 0.0
    ui_blocks: List[Any] = Field(default_factory=list)
    summary: Optional[str] = None


class BaseTool(ABC):
    """
    Base class for all DI tools.

    Subclasses must define:
        name: str           — unique tool identifier (snake_case)
        description: str    — what the tool does
        parameters: list    — list of ToolParameter
        category: str       — 'academic', 'browser', 'computer', 'file', etc.

    And implement:
        execute(**kwargs) -> ToolResult
    """

    name: str = ""
    description: str = ""
    category: str = "general"
    parameters: List[ToolParameter] = []
    ui_meta: Optional["ToolUiMeta"] = None

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool and return a ToolResult."""
        ...

    def _input_schema(self) -> Dict:
        """JSON Schema for tool parameters only (no ui_meta — avoids recursion)."""
        return {
            "type": "object",
            "properties": {
                p.name: {
                    "type": p.type,
                    "description": p.description,
                    **({"default": p.default} if p.default is not None else {}),
                }
                for p in self.parameters
            },
            "required": [p.name for p in self.parameters if p.required],
        }

    def get_ui_meta(self) -> Dict:
        """Return UI rendering metadata for the frontend tool registry."""
        from .ui_meta import resolve_tool_ui_meta

        if self.ui_meta is not None:
            meta = self.ui_meta
        else:
            meta = resolve_tool_ui_meta(
                self.name,
                {"name": self.name, "inputSchema": self._input_schema()},
            )
        return {
            "tool_name": meta.tool_name,
            "card_type": meta.card_type,
            "widget_type": meta.widget_type,
            "icon": meta.icon,
            "streaming": meta.streaming,
        }

    def get_schema(self) -> Dict:
        """Return MCP-compatible tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "ui_meta": self.get_ui_meta(),
            "inputSchema": self._input_schema(),
        }

    def ok(self, data: Any, duration_ms: float = 0.0) -> ToolResult:
        return ToolResult(success=True, data=data, tool_name=self.name, duration_ms=duration_ms)

    def fail(self, error: str, duration_ms: float = 0.0) -> ToolResult:
        return ToolResult(success=False, error=error, tool_name=self.name, duration_ms=duration_ms)
