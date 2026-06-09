"""Tests for search, research, and antigravity-parity file tools."""

from unittest.mock import AsyncMock, patch

import pytest

from app.tools.registry import get_registry


def test_registry_includes_new_tool_categories():
    r = get_registry()
    names = {s["name"] for s in r.list_all()}
    for tool in (
        "google_web_search",
        "deep_research",
        "search_papers",
        "get_citations",
        "search_directory",
        "find_file",
        "edit_file",
    ):
        assert tool in names


async def test_google_web_search_uses_backend(monkeypatch):
    async def fake_search(query, max_results=5):
        return {
            "query": query,
            "results": [{"title": "A", "url": "https://a", "snippet": "s", "source": "test"}],
            "count": 1,
            "backend": "test",
        }

    monkeypatch.setattr(
        "app.tools.browser.google_search.web_search",
        fake_search,
    )
    result = await get_registry().execute("google_web_search", query="python asyncio")
    assert result.success
    assert result.data["backend"] == "test"
    assert result.data["count"] == 1


async def test_deep_research_orchestrates(monkeypatch):
    async def fake_search(query, max_results=5):
        return {
            "query": query,
            "results": [{"title": "Hit", "url": "https://example.com", "snippet": "x", "source": "test"}],
            "count": 1,
            "backend": "test",
        }

    monkeypatch.setattr("app.tools.browser.research.web_search", fake_search)
    monkeypatch.setattr(
        "app.tools.browser.search.FetchURLTool.execute",
        AsyncMock(
            return_value=type(
                "R",
                (),
                {
                    "success": True,
                    "data": {"content": "page body", "status_code": 200},
                },
            )()
        ),
    )
    result = await get_registry().execute("deep_research", query="async python")
    assert result.success
    assert result.data["source_count"] >= 1


async def test_search_papers_mock_semantic_scholar(monkeypatch):
    async def fake_s2_get(path, params=None):
        return {
            "data": [
                {
                    "paperId": "abc",
                    "title": "Test Paper",
                    "year": 2024,
                    "authors": [{"name": "Alice"}],
                    "citationCount": 10,
                    "url": "https://example.com",
                    "externalIds": {"DOI": "10.1/test"},
                    "abstract": "Abstract text",
                }
            ]
        }

    monkeypatch.setattr("app.tools.research.papers._s2_get", fake_s2_get)
    result = await get_registry().execute("search_papers", query="machine learning")
    assert result.success
    assert result.data["papers"][0]["title"] == "Test Paper"


async def test_find_file_in_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()

    sample = tmp_path / "hello.py"
    sample.write_text("print('hi')", encoding="utf-8")

    result = await get_registry().execute("find_file", path=str(tmp_path), name="*.py")
    assert result.success
    assert result.data["count"] == 1


def test_shell_blocks_dangerous_command():
    from app.tools.shell.workspace import is_shell_command_allowed

    ok, _ = is_shell_command_allowed("ls -la")
    assert ok
    ok, reason = is_shell_command_allowed("rm -rf /")
    assert not ok
    assert reason


def test_antigravity_capabilities_builder():
    from app.runtime.antigravity_capabilities import build_capabilities, disabled_builtin_tools

    caps = build_capabilities(enable_subagents=True, persona="main")
    if caps is not None:
        disabled = disabled_builtin_tools()
        assert isinstance(disabled, list)
