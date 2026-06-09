"""Runtime observability for Telegram: tools, MCP, flow, logs."""

from __future__ import annotations

from typing import Any, Dict, List

from ....core.config import get_settings
from ....runtime.trace import trace_recorder

_EVENT_ICON = {
    "model": "🧠",
    "agent": "🤖",
    "subagent": "🧩",
    "tool": "🔧",
    "thinking": "💭",
    "content": "✍️",
}


def format_tools() -> str:
    from ....tools.registry import get_registry

    registry = get_registry()
    by_cat: Dict[str, List[str]] = {}
    for schema in registry.list_all():
        cat = schema.get("category", "other")
        by_cat.setdefault(cat, []).append(schema["name"])

    total = sum(len(v) for v in by_cat.values())
    lines = [f"*Tools* ({total} available)", ""]
    for cat in sorted(by_cat):
        names = ", ".join(f"`{n}`" for n in sorted(by_cat[cat]))
        lines.append(f"*{cat}*\n{names}\n")
    lines.append("Agents call these automatically. Skills can restrict which apply.")
    return "\n".join(lines)


def format_mcp() -> str:
    settings = get_settings()
    lines = ["*MCP*", ""]
    lines.append(f"Enabled: {'yes' if settings.MCP_ENABLED else 'no'}")
    lines.append(f"Transport: `{settings.MCP_TRANSPORT}`")
    external = (settings.MCP_EXTERNAL_SERVERS or "").strip()
    if external:
        names = []
        for chunk in external.split(","):
            chunk = chunk.strip()
            if "=" in chunk:
                names.append(chunk.split("=", 1)[0].strip())
        if names:
            lines.append("External servers: " + ", ".join(f"`{n}`" for n in names))
    else:
        lines.append("External servers: _none configured_")
    lines.append("\nConfigure via `MCP_EXTERNAL_SERVERS` (name=command).")
    return "\n".join(lines)


def _format_turn(turn: Dict[str, Any], *, detailed: bool) -> List[str]:
    agent = turn.get("agent_id", "main")
    model = turn.get("model", "")
    tokens = turn.get("used_tokens", 0)
    duration = turn.get("duration_ms")
    head = f"*{agent}* · `{model}` · ~{tokens} tok"
    if duration is not None:
        head += f" · {duration} ms"
    lines = [head]
    if detailed:
        for ev in turn.get("events", []):
            etype = ev.get("type", "")
            if etype == "content":
                continue
            icon = _EVENT_ICON.get(etype, "•")
            label = ev.get("name") or etype
            status = ev.get("status")
            suffix = f" ({status})" if status else ""
            lines.append(f"  {icon} {etype}: {label}{suffix}")
    else:
        tools = [e.get("name") for e in turn.get("events", []) if e.get("type") == "tool"]
        if tools:
            lines.append("  tools: " + ", ".join(f"`{t}`" for t in dict.fromkeys(tools)))
    return lines


def format_flow(*, user_id: Any, chat_id: Any) -> str:
    turn = trace_recorder.last(user_id=user_id, chat_id=chat_id)
    if not turn:
        return (
            "*Agent flow*\n\nNo turns recorded yet.\n"
            "Send a message to an agent, then `/flow` shows the live tool/agent path."
        )
    lines = ["*Agent flow* — last turn", ""]
    lines.extend(_format_turn(turn, detailed=True))
    lines.append("\n_Updated after each message. Use /logs for history._")
    return "\n".join(lines)


def format_logs(*, user_id: Any, chat_id: Any, limit: int = 5) -> str:
    turns = trace_recorder.recent(user_id=user_id, chat_id=chat_id, limit=limit)
    if not turns:
        return "*Agent logs*\n\nNo recent turns recorded yet."
    lines = [f"*Agent logs* — last {len(turns)} turns", ""]
    for idx, turn in enumerate(reversed(turns), 1):
        block = _format_turn(turn, detailed=False)
        lines.append(f"{idx}. " + block[0])
        lines.extend(block[1:])
    return "\n".join(lines)
