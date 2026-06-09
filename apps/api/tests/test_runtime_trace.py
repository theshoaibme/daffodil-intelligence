"""TurnTrace recorder: ordered events, token estimate, recent/last."""

from app.runtime.trace import TraceRecorder, estimate_tokens


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 40) == 10


def test_record_turn_events(tmp_path):
    rec = TraceRecorder(path=tmp_path / "traces.json")
    turn_id = rec.begin_turn(user_id=7, chat_id="tg-7", agent_id="coding", model="gemini-2.0-flash-lite")
    rec.add_tokens(turn_id, 100)
    rec.event(turn_id, type="agent", name="coding", status="active")
    rec.event(turn_id, type="tool", name="web_search", status="active")
    rec.event(turn_id, type="tool", name="web_search", status="success")
    rec.add_tokens(turn_id, 50)
    rec.end_turn(turn_id)

    last = rec.last(user_id=7, chat_id="tg-7")
    assert last is not None
    assert last["agent_id"] == "coding"
    assert last["used_tokens"] == 150
    assert last["duration_ms"] is not None
    types = [e["type"] for e in last["events"]]
    assert "agent" in types and "tool" in types
    tool_names = [e["name"] for e in last["events"] if e["type"] == "tool"]
    assert "web_search" in tool_names


def test_recent_limits_per_key(tmp_path):
    rec = TraceRecorder(path=tmp_path / "traces.json")
    for _ in range(3):
        tid = rec.begin_turn(user_id=1, chat_id="c", agent_id="main", model="m")
        rec.end_turn(tid)
    recent = rec.recent(user_id=1, chat_id="c", limit=2)
    assert len(recent) == 2


def test_isolated_by_key(tmp_path):
    rec = TraceRecorder(path=tmp_path / "traces.json")
    a = rec.begin_turn(user_id=1, chat_id="a", agent_id="main", model="m")
    rec.end_turn(a)
    assert rec.last(user_id=2, chat_id="b") is None
    assert rec.last(user_id=1, chat_id="a") is not None
