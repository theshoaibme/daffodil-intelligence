"""Merge global config, agent profiles, custom agents, skills, and rulesets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session_maker, is_mock_database
from ..runtime.agent_factory import AgentPersona
from .repository import HubRepository


@dataclass
class RuntimeConfig:
    agent_id: str = "main"
    persona: AgentPersona = AgentPersona.MAIN
    extra_system: str = ""
    tool_names: Optional[List[str]] = None
    skill_ids: List[str] = field(default_factory=list)
    ruleset_ids: List[str] = field(default_factory=list)


async def resolve_runtime_config(
    agent_id: Optional[str] = None,
    user_id: Any = 0,
    session: Optional[AsyncSession] = None,
) -> RuntimeConfig:
    """Build the effective runtime overlay for one chat turn."""
    if session is not None:
        repo = HubRepository(session)
        return await _resolve(repo, agent_id, user_id)

    session_maker = get_session_maker()
    if session_maker is None or is_mock_database():
        from .store import (
            agent_profile_store,
            global_config_store,
            ruleset_store,
            skill_store,
        )

        return _resolve_sync(agent_id, user_id, skill_store, ruleset_store, global_config_store, agent_profile_store)

    async with session_maker() as db_session:
        repo = HubRepository(db_session)
        return await _resolve(repo, agent_id, user_id)


async def _resolve(repo: HubRepository, agent_id: Optional[str], user_id: Any) -> RuntimeConfig:
    global_cfg = await repo.get_global_config()
    effective_id = (agent_id or global_cfg.default_agent_id or "main").strip()

    ruleset_ids: List[str] = list(global_cfg.ruleset_ids)
    skill_ids: List[str] = list(global_cfg.skill_ids)
    extra_parts: List[str] = []

    if global_cfg.extra_system.strip():
        extra_parts.append(global_cfg.extra_system.strip())

    profile = await repo.get_agent_profile(effective_id)
    if profile:
        ruleset_ids.extend(profile.ruleset_ids)
        skill_ids.extend(profile.skill_ids)
        if profile.extra_system.strip():
            extra_parts.append(profile.extra_system.strip())

    persona = _resolve_persona(effective_id)
    agent_extra = _resolve_agent_prompt(effective_id)
    if agent_extra:
        extra_parts.append(agent_extra)

    custom = await _resolve_custom_agent(repo, effective_id)
    if custom:
        if custom.get("system_prompt"):
            extra_parts.append(custom["system_prompt"].strip())
        ruleset_ids.extend(custom.get("ruleset_ids") or [])
        skill_ids.extend(custom.get("skill_ids") or [])

    ruleset_ids = _dedupe(ruleset_ids)
    skill_ids = _dedupe(skill_ids)

    tool_names_acc: List[str] = []
    if custom and custom.get("tool_names"):
        tool_names_acc.extend(custom["tool_names"])
    if effective_id == "routine":
        from ..agents.routine import ROUTINE_TOOLS

        tool_names_acc.extend(ROUTINE_TOOLS)

    uid = int(user_id or 0)
    for rs_id in ruleset_ids:
        rs = await repo.get_ruleset(rs_id)
        if not rs:
            continue
        if not rs.is_public and rs.created_by not in (0, uid):
            continue
        lines = "\n".join(f"- {r}" for r in rs.rules if r.strip())
        if lines:
            extra_parts.append(f"## Ruleset: {rs.name}\n{lines}")

    for sk_id in skill_ids:
        sk = await repo.get_skill(sk_id)
        if not sk:
            continue
        if not sk.is_public and sk.created_by not in (0, uid):
            continue
        await repo.increment_skill_usage(sk_id)
        block = f"## Skill: {sk.name}\n{sk.content.strip()}"
        if sk.tool_names:
            block += "\n\nSuggested tools: " + ", ".join(f"`{t}`" for t in sk.tool_names)
            tool_names_acc.extend(sk.tool_names)
        extra_parts.append(block)

    return RuntimeConfig(
        agent_id=effective_id,
        persona=persona,
        extra_system="\n\n".join(extra_parts).strip(),
        tool_names=_dedupe(tool_names_acc) or None,
        skill_ids=skill_ids,
        ruleset_ids=ruleset_ids,
    )


def _resolve_sync(agent_id, user_id, skill_store, ruleset_store, global_config_store, agent_profile_store):
    """Fallback for mock DB / tests using sync store wrappers."""
    global_cfg = global_config_store.get()
    effective_id = (agent_id or global_cfg.default_agent_id or "main").strip()

    ruleset_ids: List[str] = list(global_cfg.ruleset_ids)
    skill_ids: List[str] = list(global_cfg.skill_ids)
    extra_parts: List[str] = []

    if global_cfg.extra_system.strip():
        extra_parts.append(global_cfg.extra_system.strip())

    profile = agent_profile_store.get(effective_id)
    if profile:
        ruleset_ids.extend(profile.ruleset_ids)
        skill_ids.extend(profile.skill_ids)
        if profile.extra_system.strip():
            extra_parts.append(profile.extra_system.strip())

    persona = _resolve_persona(effective_id)
    agent_extra = _resolve_agent_prompt(effective_id)
    if agent_extra:
        extra_parts.append(agent_extra)

    custom = _resolve_custom_agent_sync(effective_id)
    if custom:
        if custom.get("system_prompt"):
            extra_parts.append(custom["system_prompt"].strip())
        ruleset_ids.extend(custom.get("ruleset_ids") or [])
        skill_ids.extend(custom.get("skill_ids") or [])

    ruleset_ids = _dedupe(ruleset_ids)
    skill_ids = _dedupe(skill_ids)

    tool_names_acc: List[str] = []
    if custom and custom.get("tool_names"):
        tool_names_acc.extend(custom["tool_names"])
    if effective_id == "routine":
        from ..agents.routine import ROUTINE_TOOLS

        tool_names_acc.extend(ROUTINE_TOOLS)

    for rs_id in ruleset_ids:
        rs = ruleset_store.get(rs_id)
        if not rs:
            continue
        if not rs.is_public and rs.created_by not in (0, int(user_id or 0)):
            continue
        lines = "\n".join(f"- {r}" for r in rs.rules if r.strip())
        if lines:
            extra_parts.append(f"## Ruleset: {rs.name}\n{lines}")

    for sk_id in skill_ids:
        sk = skill_store.get(sk_id)
        if not sk:
            continue
        if not sk.is_public and sk.created_by not in (0, int(user_id or 0)):
            continue
        skill_store.increment_usage(sk_id)
        block = f"## Skill: {sk.name}\n{sk.content.strip()}"
        if sk.tool_names:
            block += "\n\nSuggested tools: " + ", ".join(f"`{t}`" for t in sk.tool_names)
            tool_names_acc.extend(sk.tool_names)
        extra_parts.append(block)

    return RuntimeConfig(
        agent_id=effective_id,
        persona=persona,
        extra_system="\n\n".join(extra_parts).strip(),
        tool_names=_dedupe(tool_names_acc) or None,
        skill_ids=skill_ids,
        ruleset_ids=ruleset_ids,
    )


def _dedupe(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _resolve_persona(agent_id: str) -> AgentPersona:
    if agent_id in ("computer_use", "planning"):
        return AgentPersona(agent_id)
    return AgentPersona.MAIN


def _resolve_agent_prompt(agent_id: str) -> str:
    if agent_id in ("main", "supervisor", ""):
        return ""
    try:
        from ..agents.registry import AGENT_MAP

        agent = AGENT_MAP.get(agent_id)
        if agent:
            return (
                f"You are the **{agent.name}** specialist agent.\n"
                f"Focus: {agent.description}\n"
                "Use your tools when needed and stay in this domain."
            )
    except Exception:
        pass
    return ""


def _capability_tools(capabilities: Any) -> List[str]:
    """Collect tool names declared on a custom agent's capabilities."""
    tools: List[str] = []
    for cap in capabilities or []:
        cap_tools = cap.get("tools") if isinstance(cap, dict) else getattr(cap, "tools", None)
        for t in cap_tools or []:
            if t:
                tools.append(str(t))
    return tools


async def _resolve_custom_agent(repo: HubRepository, agent_id: str) -> Optional[dict]:
    row = await repo.get_custom_agent(agent_id)
    if not row:
        return None
    skill_ids, ruleset_ids = await repo._agent_link_ids(agent_id)
    return {
        "system_prompt": row.system_prompt,
        "ruleset_ids": ruleset_ids,
        "skill_ids": skill_ids,
        "tool_names": _capability_tools(getattr(row, "capabilities", None)),
    }


def _resolve_custom_agent_sync(agent_id: str) -> Optional[dict]:
    try:
        from ..agents.builder import get_agent

        agent = get_agent(agent_id)
        if not agent:
            return None
        return {
            "system_prompt": agent.system_prompt,
            "ruleset_ids": getattr(agent, "ruleset_ids", None) or [],
            "skill_ids": getattr(agent, "skill_ids", None) or [],
            "tool_names": _capability_tools(getattr(agent, "capabilities", None)),
        }
    except Exception:
        return None
