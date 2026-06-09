"""Skills CRUD for Telegram, backed by the skills hub store."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ....skills.store import skill_store


def create_skill(
    *,
    owner_id: int,
    name: str,
    content: str,
    tool_names: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    name = (name or "").strip()
    if len(name) < 2:
        return False, "Skill name must be at least 2 characters."
    if not (content or "").strip():
        return False, "Skill content is required."
    skill = skill_store.create(
        name=name,
        description=name,
        content=content.strip(),
        tool_names=tool_names or [],
        tags=tags or [],
        created_by=owner_id,
        is_public=False,
    )
    tools = ", ".join(f"`{t}`" for t in (tool_names or [])) or "none"
    return True, (
        f"Created skill *{skill.name}*\n"
        f"ID: `{skill.id}`\n"
        f"Tools: {tools}\n\n"
        f"Assign to an agent with `/agentskills <agent_id> {skill.id}`."
    )


def update_skill(
    skill_id: str,
    owner_id: int,
    *,
    name: Optional[str] = None,
    content: Optional[str] = None,
    tool_names: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    skill = skill_store.get(skill_id)
    if not skill:
        return False, f"No skill `{skill_id}`."
    if not (skill.is_public or skill.created_by in (0, owner_id)):
        return False, "You can only edit skills you created."
    fields = {}
    if name:
        fields["name"] = name.strip()
    if content:
        fields["content"] = content.strip()
    if tool_names is not None:
        fields["tool_names"] = tool_names
    updated = skill_store.update(skill_id, **fields)
    if not updated:
        return False, "Update failed."
    return True, f"Updated skill *{updated.name}* (`{updated.id}`)."


def delete_skill(skill_id: str, owner_id: int) -> Tuple[bool, str]:
    skill = skill_store.get(skill_id)
    if not skill:
        return False, f"No skill `{skill_id}`."
    if not (skill.is_public or skill.created_by in (0, owner_id)):
        return False, "You can only delete skills you created."
    if skill_store.delete(skill_id):
        return True, f"Deleted skill `{skill_id}`."
    return False, "Delete failed."


def format_skill_list(owner_id: int) -> str:
    skills = skill_store.list_all(user_id=owner_id, limit=50)
    if not skills:
        return (
            "*Skills*\n\nNo skills yet.\n"
            "Create one with `/createskill <name> | <content> | tool1,tool2`."
        )
    lines = ["*Skills*", ""]
    for sk in skills[:40]:
        tools = f" · tools: {len(sk.tool_names)}" if sk.tool_names else ""
        lines.append(f"• `{sk.id}` — *{sk.name}*{tools}")
    lines.extend(
        [
            "",
            "`/createskill` · `/editskill <id>` · `/deleteskill <id>`",
            "`/agentskills <agent_id> <skill_id...>` to assign.",
        ]
    )
    return "\n".join(lines)


def format_skill_info(skill_id: str) -> str:
    skill = skill_store.get(skill_id)
    if not skill:
        return f"No skill `{skill_id}`."
    tools = ", ".join(f"`{t}`" for t in skill.tool_names) or "none"
    return (
        f"*{skill.name}* (`{skill.id}`)\n"
        f"Tools: {tools}\n"
        f"Used: {skill.usage_count}\n\n"
        f"{(skill.content or '')[:600]}"
    )
