"""Tests for routine MCP metadata wiring."""

from app.automation.routine_mcp import ensure_mcp_in_metadata, routine_turn
from app.core.config import get_settings


def test_routine_turn_detects_class_routine():
    assert routine_turn("show my class routine") is True
    assert routine_turn("hello") is False


def test_ensure_mcp_for_agent_mode(monkeypatch):
    monkeypatch.setattr(get_settings(), "MCP_ENABLED", True)
    meta = ensure_mcp_in_metadata({"selected_tools": ["Agent"]}, "hello")
    assert "MCP" in meta["selected_tools"]


def test_ensure_mcp_for_routine_message(monkeypatch):
    monkeypatch.setattr(get_settings(), "MCP_ENABLED", True)
    meta = ensure_mcp_in_metadata({"selected_tools": ["Planning"]}, "class routine Monday")
    assert "MCP" in meta["selected_tools"]
