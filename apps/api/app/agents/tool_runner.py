"""Execute registry tools and format user-facing replies."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..tools.base import ToolResult
from ..tools.registry import get_registry


def _uid(context: Optional[dict]) -> int:
    return int((context or {}).get("user_id") or 0)


def format_class_routine(data: Dict[str, Any]) -> str:
    sec = data.get("section", "")
    weekly = data.get("weekly") or {}
    if data.get("day"):
        items = data.get("items") or []
        if not items:
            return f"No classes on **{data.get('day')}** for section `{sec}`."
        lines = [f"📅 **{data.get('day')} — {sec}**"]
        for it in items:
            lines.append(
                f"• {it['time']} — {it.get('course', '')} {it.get('title', '')} "
                f"({it.get('room', '')}, {it.get('teacher', '')})"
            )
        return "\n".join(lines)

    if not weekly or all(not v for v in weekly.values()):
        return f"No routine data for section `{sec}` yet. Try e.g. `64_I`."

    lines = [f"📅 **Class routine — {sec}**"]
    for day, items in weekly.items():
        if not items:
            continue
        lines.append(f"\n**{day}**")
        for it in items:
            lines.append(
                f"• {it['time']} — {it.get('course', '')} {it.get('title', '')} "
                f"({it.get('room', '')}, {it.get('teacher', '')})"
            )
    return "\n".join(lines)


def format_reminders(data: Dict[str, Any]) -> str:
    items = data.get("reminders") or []
    if not items:
        return "You have no active reminders."
    lines = ["🔔 **Your reminders**"]
    for r in items:
        lines.append(f"• `{r.get('id')}` — {r.get('title')} @ {r.get('fire_at')} ({r.get('repeat')})")
    return "\n".join(lines)


def format_personal_routines(data: Dict[str, Any]) -> str:
    items = data.get("routines") or []
    if not items:
        return "No personal routines saved yet."
    lines = ["🗓️ **Your routines**"]
    for r in items:
        tasks = r.get("tasks") or []
        task_lines = "\n".join(f"   • {t}" for t in tasks[:5])
        lines.append(f"• **{r.get('name')}** ({r.get('schedule')})\n{task_lines}")
    return "\n".join(lines)


def format_tool_results(results: List[ToolResult]) -> str:
    parts: List[str] = []
    for r in results:
        if not r.success:
            parts.append(f"⚠️ {r.error or 'Tool failed'}")
            continue
        data = r.data or {}
        if "weekly" in data or "items" in data:
            parts.append(format_class_routine(data))
        elif "reminders" in data:
            parts.append(format_reminders(data))
        elif "routines" in data:
            parts.append(format_personal_routines(data))
        elif "reminder" in data:
            rec = data["reminder"]
            parts.append(f"✅ Reminder scheduled: **{rec.get('title')}** at {rec.get('fire_at')}")
        elif "status" in data and data.get("section"):
            parts.append(
                f"✅ Routine automation enabled for section `{data.get('section')}`."
            )
        elif "hooks" in data:
            hooks = data["hooks"]
            if not hooks:
                parts.append("No automation hooks configured.")
            else:
                lines = ["⚡ **Automation hooks**"]
                for h in hooks:
                    lines.append(f"• `{h.get('id')}` {h.get('name')} — {h.get('event')} → {h.get('action')}")
                parts.append("\n".join(lines))
        elif "hook" in data:
            h = data["hook"]
            parts.append(f"✅ Hook created: **{h.get('name')}** (`{h.get('event')}`)")
        elif "schedule" in data:
            parts.append(data.get("summary") or str(data))
        else:
            parts.append(str(data))
    return "\n\n".join(p for p in parts if p)


async def run_tool(name: str, context: Optional[dict] = None, **kwargs) -> ToolResult:
    uid = _uid(context)
    if uid and "user_id" not in kwargs:
        kwargs["user_id"] = str(uid)
    return await get_registry().execute(name, **kwargs)
