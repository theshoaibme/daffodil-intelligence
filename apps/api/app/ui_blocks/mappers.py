"""Map ToolResult payloads to generic UI blocks (no domain-specific schemas)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_TIME_SORT_RE = re.compile(r"(\d{1,2})[:.](\d{2})")

from ..tools.base import ToolResult
from .schemas import TurnPresentation, UiBlock

_ROUTINE_COL_ORDER = ("time", "course", "room", "teacher", "type", "day")
_ROUTINE_COL_LABELS = {
    "time": "Time",
    "course": "Course",
    "room": "Room",
    "teacher": "Teacher",
    "type": "Type",
    "day": "Day",
}


def _is_routine_row(row: Dict[str, Any]) -> bool:
    return bool(row.get("time") or row.get("course"))


def _ordered_row_keys(rows: List[Dict[str, Any]]) -> List[str]:
    keys: List[str] = []
    for key in _ROUTINE_COL_ORDER:
        if any(key in row for row in rows):
            keys.append(key)
    for row in rows:
        for key in row.keys():
            if key not in keys:
                keys.append(key)
    return keys


def _time_sort_key(time_str: str) -> tuple:
    match = _TIME_SORT_RE.search(str(time_str or ""))
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (99, 99)


def _sort_routine_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda r: _time_sort_key(str(r.get("time") or "")))


def _block(
    schema: str,
    data: Dict[str, Any],
    *,
    title: Optional[str] = None,
    source: Optional[str] = None,
) -> UiBlock:
    return UiBlock(block_type=schema, title=title, data=data, source=source)


def _table_from_rows(
    rows: List[Dict[str, Any]],
    *,
    title: Optional[str],
    source: Optional[str],
    empty_message: str,
) -> UiBlock:
    if not rows:
        return _block(
            "status_card",
            {"tone": "info", "message": empty_message},
            title=title,
            source=source,
        )
    display_rows = _sort_routine_rows(rows) if any(_is_routine_row(r) for r in rows) else rows
    keys = _ordered_row_keys(display_rows) if any(_is_routine_row(r) for r in display_rows) else []
    if not keys:
        for row in display_rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
    columns = [
        {"key": k, "label": _ROUTINE_COL_LABELS.get(k, k.replace("_", " ").title())}
        for k in keys
    ]
    return _block(
        "data_table",
        {"columns": columns, "rows": display_rows},
        title=title,
        source=source,
    )


def _flatten_weekly(weekly: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for day, items in weekly.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                rows.append({"day": day, **item})
    return rows


def _map_dict_to_blocks(data: Dict[str, Any], source: Optional[str], tool_name: str) -> List[UiBlock]:
    blocks: List[UiBlock] = []

    weekly = data.get("weekly")
    if isinstance(weekly, dict) and weekly:
        sec = data.get("section") or ""
        title = f"Class routine — {sec}".strip(" —") if sec else "Class routine"
        rows = _flatten_weekly(weekly)
        blocks.append(
            _table_from_rows(
                rows,
                title=title,
                source=source,
                empty_message="No routine data yet.",
            )
        )
        return blocks

    if data.get("day") and ("classes" in data or tool_name == "get_daily_schedule"):
        day = data.get("day") or "Today"
        sec = data.get("section") or ""
        base = f"{day}" + (f" · {sec}" if sec else "")
        for key, label in (("classes", "Classes"), ("reminders", "Reminders"), ("routines", "Routines")):
            lst = data.get(key)
            if isinstance(lst, list) and lst:
                blocks.append(
                    _table_from_rows(
                        lst,
                        title=f"{base} — {label}",
                        source=source,
                        empty_message=f"No {label.lower()}.",
                    )
                )
        if not blocks:
            blocks.append(
                _block(
                    "status_card",
                    {"tone": "info", "message": "Nothing scheduled."},
                    title=base,
                    source=source,
                )
            )
        return blocks

    if data.get("day") and isinstance(data.get("items"), list):
        sec = data.get("section") or ""
        day = data.get("day") or "Day"
        title = f"Class routine — {day}" + (f" · {sec}" if sec else "")
        blocks.append(
            _table_from_rows(
                data["items"],
                title=title,
                source=source,
                empty_message=f"No classes on {day}.",
            )
        )
        return blocks

    for key in ("reminders", "routines", "hooks", "agents"):
        lst = data.get(key)
        if isinstance(lst, list):
            blocks.append(
                _table_from_rows(
                    lst,
                    title=key.replace("_", " ").title(),
                    source=source,
                    empty_message=f"No {key.replace('_', ' ')}.",
                )
            )
            return blocks

    if "reminder" in data and isinstance(data["reminder"], dict):
        rec = data["reminder"]
        return [
            _block(
                "status_card",
                {
                    "tone": "success",
                    "message": f"Reminder scheduled: {rec.get('title')} at {rec.get('fire_at')}",
                },
                source=source,
            )
        ]

    if "hook" in data and isinstance(data["hook"], dict):
        h = data["hook"]
        return [
            _block(
                "status_card",
                {
                    "tone": "success",
                    "message": f"Hook created: {h.get('name')} ({h.get('event')})",
                },
                source=source,
            )
        ]

    if data.get("status") and data.get("section"):
        return [
            _block(
                "status_card",
                {
                    "tone": "success",
                    "message": f"Routine automation enabled for {data.get('section')}.",
                },
                source=source,
            )
        ]

    schedule = data.get("schedule")
    if isinstance(schedule, list) and schedule and isinstance(schedule[0], dict):
        return [_table_from_rows(schedule, title="Schedule", source=source, empty_message="Empty schedule.")]

    text_blob = data.get("text") or data.get("pdf_excerpt")
    if isinstance(text_blob, str) and text_blob.strip():
        sec = data.get("section") or ""
        title = "Class routine (document)" + (f" · {sec}" if sec else "")
        return [
            _block(
                "status_card",
                {"tone": "info", "message": text_blob.strip()[:2000]},
                title=title,
                source=source,
            )
        ]

    if isinstance(data.get("summary"), str) and data.get("summary").strip():
        return [
            _block(
                "status_card",
                {"tone": "info", "message": str(data["summary"]).strip()},
                source=source,
            )
        ]

    list_keys = [k for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], dict)]
    if len(list_keys) == 1:
        return [
            _table_from_rows(
                data[list_keys[0]],
                title=list_keys[0].replace("_", " ").title(),
                source=source,
                empty_message="No rows.",
            )
        ]

    flat = {k: v for k, v in data.items() if not isinstance(v, (list, dict))}
    if flat:
        rows = [{"key": k, "value": str(v)} for k, v in flat.items()]
        return [_block("key_value", {"rows": rows}, source=source)]

    return []


def _summary_for_data(tool_name: str, data: Dict[str, Any]) -> str:
    if tool_name == "get_daily_schedule" or ("classes" in data and data.get("day")):
        day = data.get("day") or "Today"
        sec = data.get("section") or ""
        n_class = len(data.get("classes") or [])
        n_rem = len(data.get("reminders") or [])
        prefix = f"{day}" + (f" — {sec}" if sec else "")
        parts = []
        if n_class:
            parts.append(f"{n_class} class{'es' if n_class != 1 else ''}")
        if n_rem:
            parts.append(f"{n_rem} reminder{'s' if n_rem != 1 else ''}")
        return f"{prefix}: {', '.join(parts)}." if parts else f"{prefix}: nothing scheduled."

    if "weekly" in data:
        sec = data.get("section") or ""
        weekly = data.get("weekly") or {}
        if not weekly or not any(weekly.values()):
            return f"No routine data for {sec} yet." if sec else "No routine data yet."
        return f"Weekly class routine for {sec}." if sec else "Weekly class routine."

    if data.get("day") and "items" in data:
        items = data.get("items") or []
        sec = data.get("section") or ""
        if not items:
            return f"No classes on {data.get('day')} for {sec}." if sec else f"No classes on {data.get('day')}."
        return f"Schedule for {data.get('day')} — {sec}." if sec else f"Schedule for {data.get('day')}."

    for key in ("reminders", "routines", "hooks"):
        if key in data and "classes" not in data:
            items = data.get(key) or []
            label = key.replace("_", " ")
            return f"No {label}." if not items else f"{len(items)} {label.rstrip('s')}(s)."

    if "reminder" in data:
        rec = data["reminder"]
        return f"Reminder scheduled: {rec.get('title')} at {rec.get('fire_at')}."
    if "hook" in data:
        return f"Hook created: {data['hook'].get('name')}."
    if data.get("status") and data.get("section"):
        return f"Routine automation enabled for {data.get('section')}."
    if tool_name:
        return f"{tool_name.replace('_', ' ')} completed."
    return "Done."


def _normalize_existing_blocks(blocks: List[UiBlock], tool_name: str) -> List[UiBlock]:
    """Re-map legacy domain blocks (routine_weekly, etc.) to generic data_table."""
    from .schemas import ALLOWED_BLOCK_SCHEMAS

    out: List[UiBlock] = []
    for block in blocks:
        if block.block_type in ALLOWED_BLOCK_SCHEMAS and block.block_type != "key_value":
            if block.block_type == "data_table" and block.data.get("rows"):
                out.append(block)
            elif block.block_type in ("status_card", "error_alert", "tabs"):
                out.append(block)
            else:
                remapped = _map_dict_to_blocks(block.data, block.source, tool_name)
                out.extend(remapped or [block])
        else:
            remapped = _map_dict_to_blocks(block.data, block.source or tool_name, tool_name)
            if remapped:
                if block.title and remapped:
                    remapped[0] = remapped[0].model_copy(update={"title": block.title})
                out.extend(remapped)
            else:
                out.append(block)
    return out


def map_tool_result(tool_name: str, result: ToolResult, *, source: Optional[str] = None) -> List[UiBlock]:
    src = source or tool_name or result.tool_name

    if not result.success:
        return [
            _block(
                "error_alert",
                {"message": result.error or "Tool failed"},
                title=tool_name or result.tool_name,
                source=src,
            )
        ]

    if result.ui_blocks:
        return _normalize_existing_blocks(list(result.ui_blocks), tool_name)

    data = result.data
    if isinstance(data, str):
        return []
    if not isinstance(data, dict):
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return [_table_from_rows(data, title=tool_name, source=src, empty_message="No rows.")]
        return []

    blocks = _map_dict_to_blocks(data, src, tool_name)
    return blocks


def enrich_tool_result(result: ToolResult, tool_name: Optional[str] = None) -> ToolResult:
    name = tool_name or result.tool_name
    blocks = map_tool_result(name, result)
    result.ui_blocks = blocks
    if not result.summary:
        if not result.success:
            result.summary = result.error or "Tool failed"
        elif isinstance(result.data, dict):
            result.summary = _summary_for_data(name, result.data)
        else:
            result.summary = _summary_for_data(name, {})
    return result


def format_tool_results(results: List[ToolResult]) -> TurnPresentation:
    summaries: List[str] = []
    blocks: List[UiBlock] = []

    for r in results:
        enriched = enrich_tool_result(r)
        if enriched.summary:
            summaries.append(enriched.summary)
        blocks.extend(enriched.ui_blocks)

    return TurnPresentation(
        summary="\n".join(s for s in summaries if s).strip(),
        blocks=blocks,
    )
