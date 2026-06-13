"""Tests for turn complexity policy."""

from app.runtime.chat_router import should_force_full_runtime, should_use_fast_groq
from app.runtime.task_policy import (
    TurnComplexity,
    classify_turn,
    should_emit_task_tree,
)


def test_should_emit_task_tree_simple_only():
    assert should_emit_task_tree(TurnComplexity.SIMPLE) is False
    assert should_emit_task_tree(TurnComplexity.TOOL) is True
    assert should_emit_task_tree(TurnComplexity.PLANNING) is True


def test_classify_simple_fast_path():
    complexity = classify_turn(
        "What is Python?",
        {"selected_tools": []},
        routing="fast_simple",
        use_fast_groq=True,
        use_hf=False,
    )
    assert complexity == TurnComplexity.SIMPLE


def test_planning_mode_forces_full_runtime():
    meta = {"selected_tools": ["Planning"], "_message": "hi"}
    assert should_force_full_runtime(meta) is True
    assert (
        should_use_fast_groq(
            routing="fast_simple",
            was_auto=True,
            metadata=meta,
        )
        is False
    )


def test_planning_mode_not_simple():
    complexity = classify_turn(
        "hi",
        {"selected_tools": ["Planning"]},
        routing="fast_simple",
        use_fast_groq=False,
        use_hf=False,
    )
    assert complexity == TurnComplexity.PLANNING


def test_research_mode_classified():
    complexity = classify_turn(
        "Tell me about async",
        {"selected_tools": ["Research"]},
        routing="default",
        use_fast_groq=False,
        use_hf=False,
    )
    assert complexity == TurnComplexity.RESEARCH

def test_should_emit_task_tree_research_and_multi_agent():
    assert should_emit_task_tree(TurnComplexity.RESEARCH) is True
    assert should_emit_task_tree(TurnComplexity.MULTI_AGENT) is True


def test_should_force_full_runtime_modes():
    assert should_force_full_runtime({"selected_tools": ["Research"]}) is True
    assert should_force_full_runtime({"selected_tools": ["Agent"]}) is True
    assert should_force_full_runtime({"selected_tools": []}) is False
    assert should_force_full_runtime(None) is False


def test_classify_multi_agent_from_message():
    complexity = classify_turn(
        "parallel_invoke agents for foo and bar",
        {"selected_tools": []},
        routing="default",
        use_fast_groq=False,
        use_hf=False,
    )
    assert complexity == TurnComplexity.MULTI_AGENT


def test_classify_planning_from_multi_step_text():
    complexity = classify_turn(
        "First search docs then summarize",
        {"selected_tools": []},
        routing="default",
        use_fast_groq=False,
        use_hf=False,
    )
    assert complexity == TurnComplexity.PLANNING


def test_classify_research_keyword_without_mode():
    complexity = classify_turn(
        "Please compare Python versus Rust for backends",
        {"selected_tools": []},
        routing="default",
        use_fast_groq=False,
        use_hf=False,
    )
    assert complexity == TurnComplexity.RESEARCH
