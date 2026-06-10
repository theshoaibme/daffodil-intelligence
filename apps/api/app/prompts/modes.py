"""Mode-based system prompt overlays for chat UI modes and auto routing."""

from __future__ import annotations

from typing import Optional

_MODE_INSTRUCTIONS: dict[str, str] = {
    "Planning": """MODE: PLANNING
- Break goals into numbered, actionable steps.
- State assumptions and dependencies clearly.
- Prefer structured plans over long prose.
- End with a short "Next actions" list when appropriate.""",
    "Research": """MODE: RESEARCH
- Gather accurate information before concluding.
- Prefer tools and sources over guessing.
- Summarize findings with bullet points.
- Call out uncertainty when evidence is thin.""",
    "MCP": """MODE: MCP TOOLS
- Use configured MCP integrations when they help answer the request.
- For class routines: call get_class_routine, read_department_routine_pdf, recall_notes.
- Prefer tool results over invented data.
- Explain which tool was used and what it returned.""",
    "Agent": """MODE: MULTI-AGENT
- Coordinate specialized agents when the task spans domains.
- For schedules/routines: invoke_agent(agent_type="routine") or MCP tools directly.
- Delegate with invoke_agent when a sub-task fits a specialist.
- Synthesize agent outputs into one clear answer.""",
}

_CHAT_DEFAULT = """MODE: CHAT
- Answer directly and concisely unless the user asks for detail.
- Be accurate; say when you are unsure.
- Use Markdown when it improves readability."""

_ROUTING_HINTS: dict[str, str] = {
    "groq_fast": "Runtime: fast Groq model for quick replies.",
    "fast_simple": "Runtime: fast path for a short, simple question.",
    "default": "Runtime: standard chat path.",
    "complex": "Runtime: stronger model for a broader question.",
    "code": "Runtime: code-capable model.",
    "code_complex": "Runtime: advanced model for complex code/architecture.",
    "reasoning": "Runtime: reasoning-focused model.",
    "long_context": "Runtime: model tuned for long input.",
    "attachments": "Runtime: multimodal model for attachments.",
}


def active_modes(metadata: Optional[dict]) -> list[str]:
    if not metadata:
        return []
    tools = metadata.get("selected_tools") or []
    return [m for m in ("Planning", "Research", "MCP", "Agent") if m in tools]


def build_mode_system_prompt(
    metadata: Optional[dict],
    *,
    routing: str = "default",
    model_id: str = "",
    engine: str = "antigravity",
) -> str:
    """Compose the mode + routing overlay injected into extra_system."""
    parts: list[str] = []
    modes = active_modes(metadata)

    if modes:
        parts.append("ACTIVE USER MODES (honor all that apply):")
        for mode in modes:
            block = _MODE_INSTRUCTIONS.get(mode)
            if block:
                parts.append(block)
    else:
        parts.append(_CHAT_DEFAULT)

    routing_hint = _ROUTING_HINTS.get(routing, "")
    if routing_hint:
        parts.append(routing_hint)

    if model_id:
        parts.append(f"Selected model: {model_id} ({engine}).")

    return "\n\n".join(parts)


def mode_status_messages(
    metadata: Optional[dict],
    *,
    routing: str,
    model_id: str,
    engine: str,
) -> list[str]:
    """Short system status lines streamed to the client in real time."""
    lines: list[str] = []
    modes = active_modes(metadata)
    if modes:
        labels = ", ".join(modes)
        lines.append(f"Mode: {labels}")
    else:
        lines.append("Mode: Chat")

    if routing == "groq_fast":
        lines.append(f"Fast model selected — {model_id}")
    elif routing in ("code", "code_complex", "reasoning", "long_context"):
        lines.append(f"Upgraded model for {routing.replace('_', ' ')} — {model_id}")
    else:
        lines.append(f"Model: {model_id}")

    lines.append(f"Engine: {engine}")
    return lines
