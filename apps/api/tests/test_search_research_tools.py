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


async def test_deep_research_parallel_group_shared(monkeypatch):
    """Subqueries share one parallel_group and run via asyncio.gather."""
    gather_calls: list = []
    original_gather = __import__("asyncio").gather

    async def tracking_gather(*coros, **kwargs):
        gather_calls.append(len(coros))
        return await original_gather(*coros, **kwargs)

    monkeypatch.setattr("app.tools.browser.research.asyncio.gather", tracking_gather)

    async def fake_search(query, max_results=5):
        return {
            "query": query,
            "results": [{"title": "Hit", "url": f"https://example.com/{query[:8]}", "snippet": "x", "source": "test"}],
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

    from app.runtime.task_events import reset_turn_tasks, take_nested_events

    reset_turn_tasks()
    result = await get_registry().execute(
        "deep_research",
        query="async python; asyncio patterns; rust ownership",
        max_subqueries=3,
    )
    assert result.success
    assert gather_calls == [3]

    events = [e for e in take_nested_events() if e.get("type") == "task" and e.get("name") == "subquery"]
    groups = {e.get("parallel_group") for e in events}
    assert len(groups) == 1
    assert result.data.get("parallel_group") == next(iter(groups))


async def test_deep_research_orchestrates(monkeypatch):
    gather_calls = {"count": 0}
    real_gather = __import__("asyncio").gather

    async def tracking_gather(*coros, **kwargs):
        gather_calls["count"] += 1
        return await real_gather(*coros, **kwargs)

    async def fake_search(query, max_results=5):
        return {
            "query": query,
            "results": [{"title": "Hit", "url": "https://example.com", "snippet": "x", "source": "test"}],
            "count": 1,
            "backend": "test",
        }

    monkeypatch.setattr("app.tools.browser.research.asyncio.gather", tracking_gather)
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
    from app.runtime.task_events import reset_turn_tasks, take_nested_events

    reset_turn_tasks()
    result = await get_registry().execute(
        "deep_research",
        query="async python; rust patterns",
    )
    assert result.success
    assert result.data["source_count"] >= 1
    assert gather_calls["count"] >= 1
    assert result.data.get("parallel_group")

    events = take_nested_events()
    subquery_events = [
        e for e in events if e.get("type") == "task" and e.get("name") == "subquery"
    ]
    groups = {e.get("parallel_group") for e in subquery_events if e.get("parallel_group")}
    assert len(groups) == 1


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
