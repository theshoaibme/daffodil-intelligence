"""
Agent Factory
=============
Builds configured Google Daffodil Intelligence ``Agent`` instances for each persona used
by Daffodil Intelligence (main orchestrator, computer-use, planning).

The factory wires together:
  - system instructions (``prompts.manager``)
  - tools (``runtime.tool_adapter`` over the BaseTool registry)
  - policies (``runtime.policies``)
  - MCP servers (``mcp.servers`` when available)
  - Gemini config (from settings.GEMINI_API_KEY)
  - per-conversation persistence (conversation_id + save_dir)
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

from ..core.config import get_settings
from ..prompts.manager import get_system_instructions
from .antigravity_capabilities import build_capabilities
from .tool_adapter import get_antigravity_tools
from .policies import build_policies

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig, GeminiConfig
    _ANTIGRAVITY_AVAILABLE = True
except Exception as e:  # pragma: no cover - import guard
    Agent = None  # type: ignore
    LocalAgentConfig = None  # type: ignore
    CapabilitiesConfig = None  # type: ignore
    GeminiConfig = None  # type: ignore
    _ANTIGRAVITY_AVAILABLE = False
    logger.error(f"google-antigravity SDK unavailable: {e}")


class AgentPersona(str, Enum):
    MAIN = "main"
    COMPUTER_USE = "computer_use"
    PLANNING = "planning"
    RESEARCH = "research"


# Tool categories available to each persona.
_PERSONA_TOOL_CATEGORIES = {
    AgentPersona.MAIN: None,  # all tools
    AgentPersona.COMPUTER_USE: ["computer"],
    AgentPersona.PLANNING: None,
    AgentPersona.RESEARCH: ["browser", "research", "memory", "file"],
}


def is_available() -> bool:
    """Whether the Daffodil Intelligence SDK and a Gemini key are both present."""
    return _ANTIGRAVITY_AVAILABLE and bool(settings.GEMINI_API_KEY)


def _get_mcp_servers() -> List[Any]:
    """Best-effort load of MCP server configs for the agent to consume."""
    try:
        from ..mcp.servers import get_mcp_server_configs
        from ..mcp.user_store import get_user_specs
        from .tool_context import get_selected_tools, get_turn_mcp_specs, get_user_id

        if not settings.MCP_ENABLED:
            return []

        selected = get_selected_tools()
        turn_specs = get_turn_mcp_specs()

        wants_mcp = (
            not selected
            or "MCP" in selected
            or "Agent" in selected
            or "Planning" in selected
            or bool(turn_specs)
        )
        if not wants_mcp:
            return []

        extra = turn_specs or get_user_specs(get_user_id())
        include_self = (
            "MCP" in selected
            or "Agent" in selected
            or "Planning" in selected
            or not extra
        )
        return get_mcp_server_configs(
            include_self=include_self,
            extra_specs=extra or None,
        )
    except Exception as e:
        logger.debug(f"No MCP servers wired: {e}")
        return []


def get_save_dir() -> str:
    """Return (creating if needed) the directory where conversations persist."""
    base = Path(settings.ANTIGRAVITY_SAVE_DIR)
    base.mkdir(parents=True, exist_ok=True)
    return str(base)


def build_agent(
    persona: AgentPersona | str = AgentPersona.MAIN,
    conversation_id: Optional[str] = None,
    mode: Optional[str] = None,
    lang: Optional[str] = None,
    extra_system: Optional[str] = None,
    enable_mcp: bool = True,
    model: Optional[str] = None,
    include_tools: Optional[List[str]] = None,
):
    """Construct (but do not start) a Daffodil Intelligence ``Agent`` for a persona.

    The returned object is an async context manager: use ``async with``.

    Raises:
        RuntimeError: if the SDK or GEMINI_API_KEY is unavailable.
    """
    if not _ANTIGRAVITY_AVAILABLE:
        raise RuntimeError("google-antigravity SDK is not installed.")
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    persona = AgentPersona(persona) if not isinstance(persona, AgentPersona) else persona

    system_instructions = get_system_instructions(persona.value, mode=mode, lang=lang)
    if extra_system:
        system_instructions = f"{system_instructions}\n\n{extra_system}"

    categories = _PERSONA_TOOL_CATEGORIES.get(persona)
    tools = get_antigravity_tools(categories=categories, include=include_tools)

    policies = build_policies(persona.value)

    mcp_servers = _get_mcp_servers() if enable_mcp else []

    enable_subagents = (
        settings.ANTIGRAVITY_ENABLE_SUBAGENTS and persona != AgentPersona.COMPUTER_USE
    )
    capabilities = build_capabilities(
        enable_subagents=enable_subagents,
        persona=persona.value,
    )
    if capabilities is None and _ANTIGRAVITY_AVAILABLE:
        capabilities = CapabilitiesConfig(enable_subagents=enable_subagents)

    config_kwargs: dict[str, Any] = {
        "system_instructions": system_instructions,
        "capabilities": capabilities,
        "tools": tools,
        "policies": policies,
        "gemini_config": GeminiConfig(api_key=settings.GEMINI_API_KEY),
        "model": model or settings.ANTIGRAVITY_MODEL,
        "save_dir": get_save_dir(),
    }
    if mcp_servers:
        config_kwargs["mcp_servers"] = mcp_servers
    # Only resume an EXISTING conversation; a fresh agent gets a new id assigned
    # by the SDK (read back via agent.conversation_id afterwards).
    if conversation_id:
        config_kwargs["conversation_id"] = conversation_id

    config = LocalAgentConfig(**config_kwargs)
    logger.info(
        f"Built Antigravity agent persona={persona.value} model={config_kwargs['model']} "
        f"tools={len(tools)}{'(filtered)' if include_tools else ''} policies={len(policies)} "
        f"mcp={len(mcp_servers)} conv={conversation_id}"
    )
    return Agent(config)
