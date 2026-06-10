"""Tool → agent mapping for accurate flow simulation and task events."""

from __future__ import annotations

from typing import Dict, List

# Multiple agents may legitimately use the same tool.
TOOL_AGENTS: Dict[str, List[str]] = {
    # Orchestration / delegation
    "invoke_agent": ["planning"],
    "parallel_invoke_agents": ["planning"],
    "list_agents": ["planning"],
    # Research & web
    "deep_research": ["research"],
    "google_web_search": ["research"],
    "web_search": ["research"],
    "fetch_url": ["research"],
    "search_papers": ["research"],
    "get_citations": ["research"],
    # Coding & shell
    "run_shell_command": ["coding"],
    "run_python": ["coding"],
    # Writing & files
    "read_file": ["writing"],
    "write_file": ["writing"],
    "edit_file": ["writing"],
    "list_directory": ["writing"],
    "search_directory": ["writing"],
    "find_file": ["writing"],
    "delete_file": ["writing"],
    "read_pdf": ["writing", "routine"],
    # Tasks & schedules (personal productivity)
    "schedule_task": ["tasks"],
    "get_daily_schedule": ["tasks"],
    "create_routine": ["tasks"],
    "list_routines": ["tasks"],
    "delete_routine": ["tasks"],
    # Class routines (university — still highlight when used)
    "get_class_routine": ["routine"],
    "read_routine_pdf": ["routine"],
    "read_department_routine_pdf": ["routine"],
    "enable_routine_automation": ["routine"],
    "create_reminder": ["routine", "tasks"],
    "list_reminders": ["routine", "tasks"],
    "delete_reminder": ["routine", "tasks"],
    # Notifications
    "send_telegram_message": ["notification"],
    # Memory
    "recall_notes": ["planning"],
    "store_note": ["planning"],
    "list_memories": ["planning"],
    # Computer
    "take_screenshot": ["computer_use"],
    "mouse_move": ["computer_use"],
    "mouse_click": ["computer_use"],
    "mouse_scroll": ["computer_use"],
    "keyboard_type": ["computer_use"],
    "keyboard_hotkey": ["computer_use"],
    "start_recording": ["copycat"],
    "stop_recording": ["copycat"],
    "replay_recording": ["copycat"],
    # University domain tools
    "get_cgpa": ["academic"],
    "get_courses": ["academic"],
    "get_attendance": ["academic"],
    "get_exam_schedule": ["exam"],
    "search_books": ["library"],
    "get_book_availability": ["library"],
    "get_shuttle_schedule": ["transport"],
    "get_jobs": ["career"],
    "get_internships": ["career"],
}

PRODUCTIVITY_AGENT_IDS = frozenset(
    {"coding", "research", "writing", "tasks", "notification"}
)


def agents_for_tool(tool_name: str, *, invoke_agent_id: str | None = None) -> List[str]:
    """Resolve which agent node(s) should highlight for a tool call."""
    key = (tool_name or "").strip().lower()
    found: List[str] = []
    if key in TOOL_AGENTS:
        found.extend(TOOL_AGENTS[key])
    if invoke_agent_id:
        found.append(invoke_agent_id.strip().lower())
    if key.startswith("memory_") or key in ("recall_notes", "store_note"):
        if "planning" not in found:
            found.append("planning")
    # Heuristic fallbacks
    if "research" in key and "research" not in found:
        found.append("research")
    if "routine" in key or "reminder" in key:
        for aid in ("routine", "tasks"):
            if aid not in found:
                found.append(aid)
    if key in ("read_pdf", "read_file", "write_file", "edit_file") and "writing" not in found:
        found.append("writing")
    return list(dict.fromkeys(a for a in found if a))
