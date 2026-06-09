"""Agent Hub CRUD for Telegram: create / edit / delete / subagent / skills."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ....agents.builder import (
    AgentBuilder,
    delete_agent,
    get_agent,
    list_agents,
    register_agent,
)
from ....agents.registry import AGENT_MAP


def _owned(agent, owner_id: int) -> bool:
    return agent.created_by in (0, owner_id) or agent.is_public


def create_custom_agent(
    *,
    owner_id: int,
    name: str,
    description: str,
    system_prompt: str = "",
    skill_ids: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    name = (name or "").strip()
    if len(name) < 2:
        return False, "Agent name must be at least 2 characters."
    agent = AgentBuilder.create_agent(
        name=name,
        description=(description or "").strip() or name,
        custom_prompt=(system_prompt or "").strip() or None,
        created_by=owner_id,
    )
    if skill_ids:
        agent.skill_ids = skill_ids
    register_agent(agent)
    return True, (
        f"Created agent *{agent.name}*\n"
        f"ID: `{agent.id}`\n\n"
        f"Switch to it with `/agent {agent.id}`."
    )


def create_subagent(
    *,
    owner_id: int,
    parent_id: str,
    name: str,
    description: str,
    instructions: str = "",
) -> Tuple[bool, str]:
    parent_name = agent_display_name(parent_id)
    if parent_name is None:
        return False, f"Unknown parent agent `{parent_id}`. Send /agents to list."
    prompt = (
        f"You are *{name}*, a sub-agent of {parent_name}.\n"
        f"Role: {description}\n"
    )
    if instructions.strip():
        prompt += f"\nInstructions:\n{instructions.strip()}\n"
    prompt += "\nStay focused on your delegated task and report concise results."
    ok, msg = create_custom_agent(
        owner_id=owner_id,
        name=name,
        description=f"Subagent of {parent_name}: {description}",
        system_prompt=prompt,
    )
    if ok:
        msg += f"\n\nParent: `{parent_id}`. Invoke via the parent or `/agent <id>`."
    return ok, msg


def update_custom_agent(
    agent_id: str,
    owner_id: int,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> Tuple[bool, str]:
    agent = get_agent(agent_id)
    if not agent:
        return False, f"No custom agent `{agent_id}`. Builtin agents cannot be edited."
    if not _owned(agent, owner_id):
        return False, "You can only edit agents you created."
    if name:
        agent.name = name.strip()
    if description:
        agent.description = description.strip()
    if system_prompt:
        agent.system_prompt = system_prompt.strip()
    register_agent(agent)
    return True, f"Updated agent *{agent.name}* (`{agent.id}`)."


def delete_custom_agent(agent_id: str, owner_id: int) -> Tuple[bool, str]:
    agent = get_agent(agent_id)
    if not agent:
        return False, f"No custom agent `{agent_id}`. Builtin agents cannot be deleted."
    if not _owned(agent, owner_id):
        return False, "You can only delete agents you created."
    delete_agent(agent_id)
    return True, f"Deleted agent `{agent_id}`."


def assign_skills(agent_id: str, owner_id: int, skill_ids: List[str]) -> Tuple[bool, str]:
    agent = get_agent(agent_id)
    if not agent:
        return False, f"No custom agent `{agent_id}` to assign skills to."
    if not _owned(agent, owner_id):
        return False, "You can only modify agents you created."
    agent.skill_ids = skill_ids
    register_agent(agent)
    if skill_ids:
        return True, f"Assigned {len(skill_ids)} skill(s) to *{agent.name}*."
    return True, f"Cleared skills for *{agent.name}*."


def agent_display_name(agent_id: str) -> Optional[str]:
    key = (agent_id or "").strip()
    builtin = AGENT_MAP.get(key.lower())
    if builtin:
        return builtin.name
    custom = get_agent(key)
    if custom:
        return custom.name
    return None


def format_agent_info(agent_id: str) -> str:
    key = (agent_id or "").strip()
    builtin = AGENT_MAP.get(key.lower())
    if builtin:
        return (
            f"*{builtin.name}* (`{key.lower()}`)\n"
            f"_Builtin agent_\n\n"
            f"{builtin.description}\n\n"
            f"Tools: {', '.join(builtin.tools) if getattr(builtin, 'tools', None) else 'all'}"
        )
    custom = get_agent(key)
    if not custom:
        return f"Unknown agent `{key}`. Send /agents to list available agents."
    skills = custom.skill_ids or []
    return (
        f"*{custom.name}* (`{custom.id}`)\n"
        f"_Custom agent_\n\n"
        f"{custom.description}\n\n"
        f"Skills: {len(skills)} · Usage: {custom.usage_count}\n"
        f"System prompt:\n{(custom.system_prompt or '')[:400]}"
    )


def format_full_agent_list(owner_id: Optional[int] = None) -> str:
    lines = ["*Agents*", "", "*Builtin*"]
    for aid, agent in sorted(AGENT_MAP.items()):
        lines.append(f"• `{aid}` — {agent.name}")
    customs = list_agents(user_id=owner_id) if owner_id else list_agents()
    customs = [a for a in customs if a.id not in AGENT_MAP]
    if customs:
        lines.extend(["", "*Custom (Agent Hub)*"])
        for agent in sorted(customs, key=lambda a: a.name.lower()):
            lines.append(f"• `{agent.id}` — {agent.name}")
    lines.extend(
        [
            "",
            "`/agent <id>` switch · `/agentinfo <id>` details",
            "`/createagent` · `/editagent` · `/deleteagent` · `/createsubagent`",
        ]
    )
    return "\n".join(lines)
