"""Assistant response validation — no duplicate prose with UI tables."""

from app.runtime.response_validate import (
    content_redundant_with_blocks,
    validate_assistant_response,
)

_TABLE_BLOCK = {
    "schema": "data_table",
    "data": {
        "title": "Final Improvement Exam Routine — CSE421 Computer Graphics",
        "rows": [
            {
                "date": "14-06-2026",
                "day": "Sunday",
                "time": "01:30 PM to 03:30 PM",
                "course": "CSE421 Computer Graphics [4]",
                "room": "320 Knowledge Tower",
            }
        ],
    },
}


def test_strips_redundant_single_course_summary():
    summary = (
        "CSE421 Computer Graphics [4] — Sunday 14-06-2026, "
        "01:30 PM to 03:30 PM, Room 320 Knowledge Tower."
    )
    assert content_redundant_with_blocks(summary, [_TABLE_BLOCK])
    assert validate_assistant_response(summary, [_TABLE_BLOCK]) == ""


def test_keeps_unique_prose_with_table():
    text = "Here is your exam slot. Contact the department if the room changes."
    assert not content_redundant_with_blocks(text, [_TABLE_BLOCK])
    assert validate_assistant_response(text, [_TABLE_BLOCK]) == text


def test_keeps_multi_paragraph_synthesis_with_table():
    """Multi-paragraph research answers must not be wiped when a data table is also present."""
    synthesis = (
        "Python asyncio uses a single-threaded event loop to multiplex I/O-bound work. "
        "Threading runs parallel OS threads and suits blocking libraries.\n\n"
        "For network-heavy pipelines, asyncio often scales better; for CPU work, use processes."
    )
    assert validate_assistant_response(synthesis, [_TABLE_BLOCK]) == synthesis
