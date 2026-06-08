"""Auto-create skills from CopyCat desktop recordings."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .store import skill_store


def create_skill_from_recording(
    name: str,
    *,
    action_count: int = 0,
    duration: float = 0.0,
    created_by: int = 0,
) -> Optional[Dict[str, Any]]:
    """Turn a saved macro into a reusable skill in the skill hub."""
    if not name:
        return None

    existing = [
        s for s in skill_store.list_all(user_id=created_by)
        if s.source == "copycat" and s.recording_name == name
    ]
    if existing:
        skill = existing[0]
        skill_store.update(
            skill.id,
            description=f"Desktop macro ({action_count} actions, {duration:.1f}s)",
            content=_skill_body(name, action_count, duration),
            tool_names=["replay_recording", "list_recordings"],
        )
        return skill_store.get(skill.id).model_dump()

    skill = skill_store.create(
        name=f"CopyCat: {name}",
        description=f"Desktop macro ({action_count} actions, {duration:.1f}s)",
        content=_skill_body(name, action_count, duration),
        tool_names=["replay_recording", "list_recordings"],
        source="copycat",
        recording_name=name,
        tags=["copycat", "automation", "desktop"],
        created_by=created_by,
        is_public=False,
    )
    return skill.model_dump()


def _skill_body(name: str, action_count: int, duration: float) -> str:
    return f"""# CopyCat skill: {name}

This skill was auto-generated from a recorded desktop macro.

- **Recording name:** `{name}`
- **Actions:** {action_count}
- **Duration:** {duration:.1f}s

## How to use
When the user asks to repeat this workflow, call `replay_recording` with `name="{name}"`.
List available macros with `list_recordings` if unsure of the name.
"""
