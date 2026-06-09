"""Hooks + loops store CRUD and scheduler event firing."""

from datetime import datetime, timedelta

import pytest

from app.automation.store import AutomationStore


def test_loop_crud_and_due(tmp_path):
    store = AutomationStore(path=tmp_path / "a.json")
    loop = store.create_loop(user_id=5, name="Briefing", prompt="summarize", interval_minutes=30)
    assert loop.id

    loops = store.list_loops(user_id=5)
    assert len(loops) == 1

    # Never run -> due immediately
    due = store.due_loops(datetime.utcnow())
    assert any(lp.id == loop.id for lp in due)

    # After marking run, not due until interval elapses
    store.mark_loop_run(loop.id, datetime.utcnow())
    assert not any(lp.id == loop.id for lp in store.due_loops(datetime.utcnow()))

    # Far future -> due again
    later = datetime.utcnow() + timedelta(minutes=31)
    assert any(lp.id == loop.id for lp in store.due_loops(later))

    assert store.delete_loop(5, loop.id)
    assert not store.list_loops(user_id=5)


def test_hook_crud_and_filter(tmp_path):
    store = AutomationStore(path=tmp_path / "a.json")
    hook = store.create_hook(
        user_id=9,
        name="welcome",
        event="on_login",
        action="message",
        payload={"text": "Welcome back!"},
    )
    assert hook.id
    assert store.hooks_for_event("on_login", user_id=9)
    assert not store.hooks_for_event("on_keyword", user_id=9)
    assert store.delete_hook(9, hook.id)
    assert not store.list_hooks(user_id=9)


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "a.json"
    store = AutomationStore(path=path)
    store.create_loop(user_id=1, name="L", prompt="p", interval_minutes=10)
    store.create_hook(user_id=1, name="H", event="on_login", action="message", payload={"text": "hi"})

    reloaded = AutomationStore(path=path)
    assert len(reloaded.list_loops(user_id=1)) == 1
    assert len(reloaded.list_hooks(user_id=1)) == 1


@pytest.mark.asyncio
async def test_trigger_event_hooks_message(monkeypatch, tmp_path):
    from app.automation import scheduler_logic

    store = AutomationStore(path=tmp_path / "a.json")
    store.create_hook(
        user_id=3,
        name="kw",
        event="on_keyword",
        action="message",
        payload={"text": "Standup time!", "keyword": "standup"},
    )
    monkeypatch.setattr(scheduler_logic, "automation_store", store)

    sent = []

    async def _fake_send(chat_id, text, **kwargs):
        sent.append((chat_id, text))
        return True

    async def _fake_resolve(user_id):
        return 12345

    monkeypatch.setattr(scheduler_logic, "send_telegram_message", _fake_send)
    monkeypatch.setattr(scheduler_logic, "resolve_telegram_chat_id_for_user", _fake_resolve)

    fired = await scheduler_logic.trigger_event_hooks(
        "on_keyword", 3, telegram_chat_id=12345, keyword_text="time for standup"
    )
    assert fired == 1
    assert sent and "Standup time!" in sent[0][1]

    # Non-matching keyword does not fire
    fired_none = await scheduler_logic.trigger_event_hooks(
        "on_keyword", 3, telegram_chat_id=12345, keyword_text="hello"
    )
    assert fired_none == 0
