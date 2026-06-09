"""Tests for root-agent intent routing."""

from app.runtime.intent_router import detect_intent, route_message


def test_class_routine_routes_to_routine_agent():
    plan = route_message("give me class routine")
    assert plan.primary == "routine"
    assert "routine" in plan.agents
    assert "get_class_routine" in plan.tools


def test_section_only_routes_with_tool():
    plan = route_message("64_I")
    assert plan.primary == "routine"
    assert plan.section == "64_I"
    assert "get_class_routine" in plan.tools


def test_cgpa_routes_to_academic():
    plan = route_message("what is my cgpa")
    assert plan.primary == "academic"
    assert "academic" in plan.agents


def test_greeting_stays_general():
    plan = route_message("hello")
    assert plan.primary == "general"
    assert detect_intent("hello") == ["general"]


def test_hint_includes_section():
    hint = route_message("64_I").hint_block()
    assert "64_I" in hint
    assert "get_class_routine" in hint
