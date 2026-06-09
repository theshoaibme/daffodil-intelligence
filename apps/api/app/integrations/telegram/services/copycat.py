"""CopyCat desktop recording commands for Telegram."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ....tools.registry import get_registry

COPYCAT_HELP = (
    "*CopyCat — desktop macros*\n\n"
    "/copycat list — saved recordings\n"
    "/copycat record \\[name\\] — start recording\n"
    "/copycat stop — save recording\n"
    "/copycat replay \\<name\\> \\[speed\\]\n\n"
    "_Legacy: /recordings, /record, /replay still work._"
)


async def run_copycat_subcommand(args: List[str]) -> str:
    """Run a copycat subcommand. Returns user-facing message."""
    if not args:
        return COPYCAT_HELP

    sub = args[0].lower()
    rest = args[1:]

    if sub in ("help", "?"):
        return COPYCAT_HELP

    if sub in ("list", "recordings", "ls"):
        return await _list_recordings()

    if sub == "record":
        name = rest[0] if rest else None
        return await _start_recording(name)

    if sub == "stop":
        return await _stop_recording()

    if sub == "replay":
        if not rest:
            return "Usage: /copycat replay <name> [speed]"
        speed = 1.0
        if len(rest) > 1:
            try:
                speed = float(rest[1])
            except ValueError:
                return "Speed must be a number (e.g. 1.5)."
        return await _replay(rest[0], speed)

    return f"Unknown subcommand `{sub}`.\n\n{COPYCAT_HELP}"


async def _list_recordings() -> str:
    result = await get_registry().execute("list_recordings")
    if not result.success:
        return f"Error: {result.error}"
    recs = (result.data or {}).get("recordings", [])
    if not recs:
        return "No recordings yet.\n\nStart one with `/copycat record my_flow`."
    return "Recordings:\n" + "\n".join(f"• {r['name']}" for r in recs)


async def _start_recording(name: Optional[str]) -> str:
    result = await get_registry().execute("start_recording", name=name)
    if result.success:
        return "Recording started. Send `/copycat stop` when finished."
    return f"Error: {result.error}"


async def _stop_recording() -> str:
    result = await get_registry().execute("stop_recording")
    if not result.success:
        return f"Error: {result.error}"
    data = result.data or {}
    msg = f"Saved: {data.get('name')} ({data.get('action_count')} actions)"
    skill = data.get("skill")
    if skill:
        msg += f"\nSkill auto-created: {skill.get('name')}"
    return msg


async def _replay(name: str, speed: float) -> str:
    result = await get_registry().execute("replay_recording", name=name, speed=speed)
    return "Replay finished." if result.success else f"Error: {result.error}"
