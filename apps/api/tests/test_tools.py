"""Tool registry + Antigravity adapter tests (no LLM/network required)."""

import pytest

from app.tools.registry import get_registry
from app.runtime.tool_adapter import get_antigravity_tools, list_tool_names, adapt_tool


def test_registry_discovers_all_categories():
    r = get_registry()
    assert r.count >= 27
    cats = set(r.categories())
    for expected in {
        "academic",
        "library",
        "transport",
        "career",
        "computer",
        "file",
        "shell",
        "memory",
        "browser",
        "research",
    }:
        assert expected in cats


async def test_domain_tool_execute():
    r = get_registry()
    result = await r.execute("get_cgpa", student_id="221-15-1234")
    assert result.success
    assert "cgpa" in result.data


async def test_unknown_tool_returns_failure():
    r = get_registry()
    result = await r.execute("does_not_exist")
    assert not result.success
    assert "Unknown tool" in (result.error or "")


def test_adapter_produces_callables_with_schema():
    tools = get_antigravity_tools()
    assert len(tools) == get_registry().count
    # Each adapted tool exposes a name and (when SDK present) an input schema.
    sample = adapt_tool(get_registry().get("get_cgpa"))
    assert getattr(sample, "__name__", None) == "get_cgpa"


def test_adapter_category_filter():
    names = list_tool_names(categories=["computer"])
    assert "take_screenshot" in names
    assert "get_cgpa" not in names
