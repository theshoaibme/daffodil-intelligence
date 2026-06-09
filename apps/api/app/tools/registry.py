"""
Tool Registry
=============
Auto-discovers and registers all BaseTool subclasses.
Provides the central catalog that MCP server uses to expose tools.
"""

import importlib
import logging
import pkgutil
import time
from typing import Dict, List, Optional, Type

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Singleton registry of all available tools.

    Auto-discovers tools by importing all modules in the tools/ package.
    Each BaseTool subclass is automatically registered.

    Usage:
        registry = get_registry()
        tool = registry.get("web_search")
        result = await tool.execute(query="python async")
    """

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._auto_discover()
        return cls._instance

    def register(self, tool: BaseTool):
        """Manually register a tool instance."""
        if tool.name in self._tools:
            logger.debug(f"Tool '{tool.name}' already registered, overwriting")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name} ({tool.category})")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_all(self) -> List[Dict]:
        """Return all tool schemas."""
        return [t.get_schema() for t in self._tools.values()]

    def list_by_category(self, category: str) -> List[BaseTool]:
        """Return all tools in a category."""
        return [t for t in self._tools.values() if t.category == category]

    def categories(self) -> List[str]:
        """Return all unique categories."""
        return list(set(t.category for t in self._tools.values()))

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with given arguments."""
        tool = self.get(tool_name)
        if not tool:
            from .base import ToolResult
            return ToolResult(
                success=False,
                error=f"Unknown tool: '{tool_name}'. Available: {list(self._tools.keys())}",
                tool_name=tool_name,
            )

        start = time.monotonic()
        try:
            result = await tool.execute(**kwargs)
            result.duration_ms = round((time.monotonic() - start) * 1000, 2)
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=tool_name,
                duration_ms=round((time.monotonic() - start) * 1000, 2),
            )

    @property
    def count(self) -> int:
        return len(self._tools)

    def _auto_discover(self):
        """Auto-import all submodules to trigger tool registration.

        Resolves the tools package relative to this module so discovery works
        regardless of whether the app is imported as ``app.tools`` (uvicorn
        ``app.main:app`` from ``apps/api``) or ``apps.api.app.tools``.
        """
        tools_pkg = importlib.import_module(__package__)

        package_path = tools_pkg.__path__
        package_name = tools_pkg.__name__

        for finder, module_name, is_pkg in pkgutil.walk_packages(
            package_path, prefix=package_name + "."
        ):
            if module_name.endswith(".base") or module_name.endswith(".registry"):
                continue
            try:
                module = importlib.import_module(module_name)
                # Find all BaseTool subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseTool)
                        and attr is not BaseTool
                        and hasattr(attr, "name")
                        and attr.name
                    ):
                        instance = attr()
                        self.register(instance)
            except Exception as e:
                logger.warning(f"Could not auto-import tool module {module_name}: {e}")

        self._loaded = True
        logger.info(f"Tool registry loaded: {self.count} tools across {len(self.categories())} categories")


def get_registry() -> ToolRegistry:
    """Get the global tool registry singleton."""
    return ToolRegistry.get_instance()
