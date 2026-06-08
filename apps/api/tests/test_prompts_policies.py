"""Prompt manager + policy builder tests."""

from app.prompts.manager import get_system_instructions
from app.runtime.policies import build_policies, DESTRUCTIVE_TOOLS


def test_main_prompt_includes_capabilities():
    text = get_system_instructions("main")
    assert "DAFFODIL INTELLIGENCE" in text
    assert "tool" in text.lower()


def test_voice_prompt_language_switch():
    bn = get_system_instructions("voice", lang="bn")
    en = get_system_instructions("voice", lang="en")
    assert bn != en


def test_dev_vs_prod_mode_differs():
    dev = get_system_instructions("main", mode="dev")
    prod = get_system_instructions("main", mode="prod")
    assert dev != prod


def test_policies_gate_destructive_tools():
    # build_policies returns [] if SDK is unavailable; otherwise it must allow-all
    # and gate destructive tools.
    policies = build_policies("main")
    if not policies:
        return  # SDK not available in this environment
    names = [getattr(p, "name", "") for p in policies]
    for tool in DESTRUCTIVE_TOOLS:
        assert any(tool in n for n in names)
