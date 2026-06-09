"""Automation CRUD for Telegram: reminders, hooks, loops."""

from __future__ import annotations

from typing import Tuple

from ....automation.store import automation_store

_HOOK_EVENTS = ("on_login", "on_keyword", "on_schedule")
_HOOK_ACTIONS = ("message", "prompt", "agent")


def format_automations(user_id: int) -> str:
    reminders = automation_store.list_reminders(user_id)
    hooks = automation_store.list_hooks(user_id=user_id)
    loops = automation_store.list_loops(user_id=user_id)
    subs = automation_store.list_subscriptions(user_id=user_id)

    lines = ["*Automation*", ""]

    lines.append("*Loops* (recurring prompts)")
    if loops:
        for lp in loops:
            lines.append(f"• `{lp.id}` — {lp.name} · every {lp.interval_minutes}m")
    else:
        lines.append("_none_ — create with `/loop <minutes> | <prompt>`")

    lines.append("\n*Hooks* (event triggers)")
    if hooks:
        for h in hooks:
            lines.append(f"• `{h.id}` — {h.name} · on {h.event} → {h.action}")
    else:
        lines.append("_none_ — create with `/createhook <event> <action> | <text>`")

    lines.append("\n*Reminders*")
    if reminders:
        for r in reminders:
            lines.append(f"• `{r.id}` — {r.title} @ {r.fire_at}")
    else:
        lines.append("_none_ — your agent can set these via chat")

    if subs:
        lines.append("\n*Subscriptions*")
        for s in subs:
            lines.append(f"• `{s.id}` — {s.kind} (section {s.section})")

    lines.extend(
        [
            "",
            "Manage: `/loop`, `/createhook`, `/reminders`",
            "Delete: `/automate delete <id>`",
        ]
    )
    return "\n".join(lines)


def create_loop_from_text(user_id: int, raw: str) -> Tuple[bool, str]:
    """`<minutes> | <prompt>` or `<minutes> | <name> | <prompt>`."""
    parts = [p.strip() for p in (raw or "").split("|")]
    if len(parts) < 2 or not parts[0]:
        return False, (
            "Usage: `/loop <minutes> | <prompt>`\n"
            "e.g. `/loop 60 | summarize my unread notifications`"
        )
    try:
        minutes = int(parts[0])
    except ValueError:
        return False, "First value must be the interval in minutes, e.g. `/loop 30 | ...`."
    if minutes < 1:
        return False, "Interval must be at least 1 minute."
    if len(parts) >= 3:
        name, prompt = parts[1], parts[2]
    else:
        name, prompt = f"Loop every {minutes}m", parts[1]
    if not prompt.strip():
        return False, "A prompt is required."
    loop = automation_store.create_loop(
        user_id=user_id,
        name=name,
        prompt=prompt.strip(),
        interval_minutes=minutes,
    )
    return True, (
        f"Created loop *{loop.name}* (`{loop.id}`)\n"
        f"Runs every {loop.interval_minutes} minutes. "
        f"Delete with `/automate delete {loop.id}`."
    )


def create_hook_from_text(user_id: int, args: list) -> Tuple[bool, str]:
    """`<event> <action> | <text> [| keyword_or_hour]`."""
    if len(args) < 2:
        return False, _hook_usage()
    event = args[0].strip().lower()
    action = args[1].strip().lower()
    if event not in _HOOK_EVENTS:
        return False, f"Event must be one of: {', '.join(_HOOK_EVENTS)}.\n\n{_hook_usage()}"
    if action not in _HOOK_ACTIONS:
        return False, f"Action must be one of: {', '.join(_HOOK_ACTIONS)}.\n\n{_hook_usage()}"

    rest = " ".join(args[2:])
    segments = [s.strip() for s in rest.split("|") if s.strip()]
    text = segments[0] if segments else ""
    extra = segments[1] if len(segments) > 1 else ""

    if not text:
        return False, f"A message/prompt is required.\n\n{_hook_usage()}"

    payload: dict = {"text": text}
    if event == "on_keyword":
        if not extra:
            return False, "on_keyword needs a keyword: `... | <text> | <keyword>`."
        payload["keyword"] = extra.lower()
    elif event == "on_schedule":
        try:
            payload["hour"] = int(extra)
        except ValueError:
            return False, "on_schedule needs an hour 0-23: `... | <text> | <hour>`."

    name = f"{event}:{action}"
    hook = automation_store.create_hook(
        user_id=user_id,
        name=name,
        event=event,
        action=action,
        payload=payload,
    )
    return True, (
        f"Created hook *{hook.name}* (`{hook.id}`)\n"
        f"Trigger: {event} → {action}. Delete with `/automate delete {hook.id}`."
    )


def delete_automation(user_id: int, item_id: str) -> Tuple[bool, str]:
    if automation_store.delete_loop(user_id, item_id):
        return True, f"Deleted loop `{item_id}`."
    if automation_store.delete_hook(user_id, item_id):
        return True, f"Deleted hook `{item_id}`."
    if automation_store.delete_reminder(user_id, item_id):
        return True, f"Deleted reminder `{item_id}`."
    return False, f"No automation `{item_id}` found that you own."


def format_reminders(user_id: int) -> str:
    reminders = automation_store.list_reminders(user_id)
    if not reminders:
        return (
            "*Reminders*\n\nNo active reminders.\n"
            "Ask in chat (e.g. \"remind me at 9pm to study\") and the agent will schedule one."
        )
    lines = ["*Reminders*", ""]
    for r in reminders:
        lines.append(f"• `{r.id}` — {r.title} @ {r.fire_at} ({r.repeat})")
    lines.append("\nDelete with `/automate delete <id>`.")
    return "\n".join(lines)


def _hook_usage() -> str:
    return (
        "Usage: `/createhook <event> <action> | <text> [| keyword|hour]`\n"
        "Events: on_login, on_keyword, on_schedule\n"
        "Actions: message, prompt, agent\n"
        "Examples:\n"
        "• `/createhook on_login message | Welcome back!`\n"
        "• `/createhook on_keyword prompt | summarize today | standup`\n"
        "• `/createhook on_schedule prompt | morning briefing | 8`"
    )
