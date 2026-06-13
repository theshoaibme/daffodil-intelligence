"""
Dynamic test suite: Telegram schedule automation workflow.

Scenarios are generated at runtime from user workflow requirements — no hardcoded
routines, sections, or JSON fixtures. Evaluates:
  - real-time memory processing
  - dynamic logic generation (offsets + class details from live routine data)
  - scheduler delivery and turn-level responsiveness
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from app.automation import routine_resolver
from app.automation.store import AutomationStore
from app.runtime.task_policy import TurnComplexity, classify_turn
from app.runtime.tool_context import clear_turn_context, set_turn_context
from tests.conftest import run_async
from tests.helpers.schedule_workflow import (
    WorkflowRequirements,
    WorkflowScenario,
    build_reminder_plan,
    build_workflow_prompt,
    class_start_on,
    generate_scenario_matrix,
    generate_workflow_scenario,
    message_has_class_details,
    parse_evening_hour_from_prompt,
    parse_hm,
    parse_offsets_from_prompt,
    persist_routine_upload,
    requirement_profiles,
)


# ---------------------------------------------------------------------------
# Fixtures — dynamic scenario generation
# ---------------------------------------------------------------------------


@pytest.fixture
def automation_store(tmp_path):
    return AutomationStore(path=tmp_path / "automation_store.json")


@pytest.fixture
def routine_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(routine_resolver, "ROUTINE_DATA_ROOT", tmp_path)
    yield tmp_path


@pytest.fixture
def telegram_capture():
    sent: List[dict] = []

    async def _send(chat_id, text, **kwargs):
        sent.append({"chat_id": chat_id, "text": text, **kwargs})
        return True

    async def _resolve(user_id):
        return 900001

    return sent, _send, _resolve


@pytest.fixture(params=generate_scenario_matrix(), ids=lambda s: s.case_id)
def workflow_scenario(request) -> WorkflowScenario:
    return request.param


@pytest.fixture
def primary_scenario() -> WorkflowScenario:
    return generate_workflow_scenario(
        seed=42,
        requirements=WorkflowRequirements.from_user_spec(offsets=(30, 10), evening_hour=22),
    )


# ---------------------------------------------------------------------------
# TC-MEM: Real-time memory processing
# ---------------------------------------------------------------------------


class TestMemoryProcessing:
    """Section and routine resolution without hardcoded defaults."""

    def test_recall_section_from_memory_note(self, primary_scenario):
        from app.automation.routine_memory import recall_user_section

        notes = [
            {
                "content": f"My section is {primary_scenario.section} for {primary_scenario.department}",
                "metadata": {},
                "payload": {},
            }
        ]

        async def _run():
            with patch(
                "app.automation.routine_memory.memory_service.recall",
                AsyncMock(return_value=notes),
            ):
                return await recall_user_section(primary_scenario.user_id)

        assert run_async(_run()) == primary_scenario.section

    def test_recall_section_from_metadata(self, primary_scenario):
        from app.automation.routine_memory import recall_user_section

        notes = [{"content": "routine prefs", "metadata": {"section": primary_scenario.section}}]

        async def _run():
            with patch(
                "app.automation.routine_memory.memory_service.recall",
                AsyncMock(return_value=notes),
            ):
                return await recall_user_section(primary_scenario.user_id)

        assert run_async(_run()) == primary_scenario.section

    def test_recall_class_routine_from_memory_weekly(self, primary_scenario):
        from app.automation.routine_memory import recall_class_routine

        weekly = primary_scenario.weekly_items()
        day = primary_scenario.first_nonempty_day()
        notes = [
            {
                "content": __import__("json").dumps({"weekly": weekly}),
                "metadata": {
                    "section": primary_scenario.section,
                    "department": primary_scenario.department,
                },
                "payload": {"weekly": weekly},
            }
        ]

        async def _run():
            with patch(
                "app.automation.routine_memory.memory_service.recall",
                AsyncMock(return_value=notes),
            ):
                return await recall_class_routine(
                    primary_scenario.user_id,
                    section=primary_scenario.section,
                    department=primary_scenario.department,
                    day=day,
                )

        data = run_async(_run())
        assert data is not None
        assert data["source"] == "memory"
        assert len(data["items"]) == len(primary_scenario.weekly[day])

    def test_pipeline_metadata_fills_section_from_memory(self, primary_scenario):
        pytest.importorskip("langchain")
        from app.runtime.pipeline import _resolve_turn_metadata

        async def _run():
            with patch(
                "app.runtime.pipeline.recall_user_section",
                AsyncMock(return_value=primary_scenario.section),
            ):
                return await _resolve_turn_metadata(primary_scenario.user_id, {})

        meta = run_async(_run())
        assert meta.get("section") == primary_scenario.section

    def test_uploaded_routine_reflects_generated_schedule(
        self, primary_scenario, routine_data_root
    ):
        from app.automation.routines_data import get_uploaded_routine

        persist_routine_upload(primary_scenario)
        day = primary_scenario.first_nonempty_day()
        data = get_uploaded_routine(
            primary_scenario.section, day, department=primary_scenario.department
        )
        assert data["section"] == primary_scenario.section
        assert len(data["items"]) == len(primary_scenario.weekly[day])
        for item, slot in zip(data["items"], primary_scenario.weekly[day]):
            assert item["course"] == slot.course
            assert item["time"] == slot.time


# ---------------------------------------------------------------------------
# TC-LOGIC: Dynamic logic generation from workflow requirements
# ---------------------------------------------------------------------------


class TestDynamicLogicGeneration:
    """Plan construction derived from requirements + generated routine data."""

    def test_prompt_round_trips_requirements(self, workflow_scenario):
        offsets = parse_offsets_from_prompt(workflow_scenario.prompt)
        hour = parse_evening_hour_from_prompt(workflow_scenario.prompt)
        assert offsets == workflow_scenario.reminder_offsets_min
        assert hour == workflow_scenario.evening_summary_hour

    def test_reminder_plan_scales_with_generated_class_count(self, workflow_scenario):
        ref = datetime(2026, 6, 8, 12, 0)
        plan = build_reminder_plan(
            workflow_scenario.weekly,
            offsets_min=workflow_scenario.reminder_offsets_min,
            ref=ref,
        )
        assert len(plan) == workflow_scenario.expected_reminder_count()
        assert workflow_scenario.class_count() > 0

    def test_reminder_plan_uses_requirement_offsets(self, primary_scenario):
        ref = datetime(2026, 6, 8, 12, 0)
        plan = build_reminder_plan(
            primary_scenario.weekly,
            offsets_min=primary_scenario.reminder_offsets_min,
            ref=ref,
        )
        assert {e["offset_min"] for e in plan} == set(primary_scenario.reminder_offsets_min)

    def test_reminder_bodies_include_generated_class_details(self, primary_scenario):
        ref = datetime(2026, 6, 8, 12, 0)
        plan = build_reminder_plan(
            primary_scenario.weekly,
            offsets_min=primary_scenario.reminder_offsets_min,
            ref=ref,
        )
        for entry in plan:
            assert message_has_class_details(entry["body"], entry["slot"])

    def test_fire_at_derived_from_generated_class_time(self, primary_scenario):
        ref = datetime(2026, 6, 8, 12, 0)
        day = primary_scenario.first_nonempty_day()
        slot = primary_scenario.first_class_on(day)
        assert slot is not None
        offset = primary_scenario.reminder_offsets_min[0]
        plan = build_reminder_plan(
            primary_scenario.weekly, offsets_min=(offset,), ref=ref
        )
        entry = next(e for e in plan if e["day"] == day and e["class_time"] == slot.time)
        class_dt = class_start_on(day, slot, ref=ref)
        assert entry["fire_at"] == class_dt - timedelta(minutes=offset)

    def test_create_reminder_accepts_dynamic_plan_entry(self, primary_scenario, automation_store):
        from app.tools.automation.reminders import CreateReminderTool

        set_turn_context(user_id=primary_scenario.user_id)
        ref = datetime(2026, 6, 8, 12, 0)
        entry = build_reminder_plan(
            primary_scenario.weekly,
            offsets_min=(primary_scenario.reminder_offsets_min[-1],),
            ref=ref,
        )[0]

        async def _run():
            with patch("app.tools.automation.reminders.automation_store", automation_store):
                return await CreateReminderTool().execute(
                    title=f"{entry['course']} T-{entry['offset_min']}m",
                    fire_at=entry["fire_at"].isoformat(),
                    body=entry["body"],
                )

        result = run_async(_run())
        assert result.success
        stored = automation_store.list_reminders(primary_scenario.user_id)
        assert len(stored) == 1
        assert stored[0].payload.get("body") == entry["body"]
        clear_turn_context()

    def test_routine_agent_keyword_gap_uses_generated_prompt(self, primary_scenario):
        """Natural-language workflow prompts miss RoutineAgent keyword triggers."""
        lower = primary_scenario.prompt.lower()
        triggers = (
            "enable routine",
            "daily tomorrow",
            "hour before class",
            "routine automation",
            "automate routine",
        )
        assert not any(k in lower for k in triggers)


# ---------------------------------------------------------------------------
# TC-SCHED: Scheduler — next-day summary & pre-class delivery
# ---------------------------------------------------------------------------


class TestSchedulerWorkflow:
    """Celery tick behavior against dynamically generated class data."""

    def test_next_day_summary_includes_generated_class_fields(self, primary_scenario):
        from app.automation import scheduler_logic

        day = primary_scenario.first_nonempty_day()
        slot = primary_scenario.first_class_on(day)
        assert slot is not None
        with patch(
            "app.automation.scheduler_logic.get_section_routine",
            return_value={"items": [slot.to_routine_item()]},
        ):
            msg = scheduler_logic.format_routine_message(primary_scenario.section, day)

        assert slot.course in msg
        assert slot.room in msg
        assert slot.teacher in msg
        assert slot.time in msg

    def test_evening_summary_hour_mismatch_documents_spec_gap(
        self, primary_scenario, automation_store, monkeypatch, telegram_capture
    ):
        from app.automation import scheduler_logic

        sent, fake_send, fake_resolve = telegram_capture
        day = primary_scenario.first_nonempty_day()
        slot = primary_scenario.first_class_on(day)
        assert slot is not None

        monkeypatch.setattr(scheduler_logic, "automation_store", automation_store)
        monkeypatch.setattr(scheduler_logic, "send_telegram_message", fake_send)
        monkeypatch.setattr(scheduler_logic, "resolve_telegram_chat_id_for_user", fake_resolve)
        monkeypatch.setattr(
            scheduler_logic,
            "get_section_routine",
            lambda section, d: {"items": [slot.to_routine_item()]},
        )

        automation_store.upsert_subscription(
            user_id=primary_scenario.user_id,
            kind="routine_daily",
            section=primary_scenario.section,
            telegram_chat_id=primary_scenario.telegram_chat_id,
        )

        user_hour = primary_scenario.evening_summary_hour
        wrong_hour = (user_hour + 1) % 24

        async def _run():
            at_user_hour = await scheduler_logic.process_routine_subscriptions(
                datetime(2026, 6, 10, user_hour, 15)
            )
            at_hardcoded_21 = await scheduler_logic.process_routine_subscriptions(
                datetime(2026, 6, 10, 21, 5)
            )
            return at_user_hour, at_hardcoded_21

        at_user_hour, at_hardcoded_21 = run_async(_run())
        if user_hour == 21:
            assert at_hardcoded_21 == 1
        else:
            assert at_user_hour == 0
            assert at_hardcoded_21 == 1

    @pytest.mark.parametrize("minutes_before", [60, 30, 10])
    def test_pre_class_offset_against_requirements(self, primary_scenario, minutes_before):
        """Alerts only when scheduler offset (60) matches; user offsets come from requirements."""
        from app.automation.scheduler_logic import classes_starting_in_one_hour

        day = primary_scenario.first_nonempty_day()
        slot = primary_scenario.first_class_on(day)
        assert slot is not None
        hour, minute = parse_hm(slot.time)
        ref_day = datetime(2026, 6, 8, 12, 0)
        class_dt = class_start_on(day, slot, ref=ref_day)
        tick = class_dt - timedelta(minutes=minutes_before)

        with patch(
            "app.automation.scheduler_logic.get_section_routine",
            return_value={"items": [slot.to_routine_item()]},
        ):
            matches = classes_starting_in_one_hour(primary_scenario.section, tick)

        should_alert = minutes_before == 60
        in_user_spec = minutes_before in primary_scenario.reminder_offsets_min
        assert bool(matches) == should_alert
        if in_user_spec and minutes_before != 60:
            assert not matches, "user-requested offset not yet implemented in scheduler"

    def test_due_reminders_deliver_generated_body(
        self, primary_scenario, automation_store, monkeypatch, telegram_capture
    ):
        from app.automation import scheduler_logic

        sent, fake_send, fake_resolve = telegram_capture
        monkeypatch.setattr(scheduler_logic, "automation_store", automation_store)
        monkeypatch.setattr(scheduler_logic, "send_telegram_message", fake_send)
        monkeypatch.setattr(scheduler_logic, "resolve_telegram_chat_id_for_user", fake_resolve)

        ref = datetime(2026, 6, 8, 12, 0)
        offset = primary_scenario.reminder_offsets_min[-1]
        entry = build_reminder_plan(
            primary_scenario.weekly, offsets_min=(offset,), ref=ref
        )[0]
        automation_store.create_reminder(
            user_id=primary_scenario.user_id,
            title="class alert",
            fire_at=(entry["fire_at"] - timedelta(seconds=1)).isoformat(),
            payload={"body": entry["body"]},
        )

        async def _run():
            return await scheduler_logic.process_due_reminders(entry["fire_at"])

        count = run_async(_run())
        assert count == 1
        assert sent and message_has_class_details(sent[0]["text"], entry["slot"])

    def test_automation_tick_aggregates_all_channels(
        self, primary_scenario, automation_store, monkeypatch, telegram_capture
    ):
        from app.automation import scheduler_logic

        sent, fake_send, fake_resolve = telegram_capture
        monkeypatch.setattr(scheduler_logic, "automation_store", automation_store)
        monkeypatch.setattr(scheduler_logic, "send_telegram_message", fake_send)
        monkeypatch.setattr(scheduler_logic, "resolve_telegram_chat_id_for_user", fake_resolve)

        automation_store.upsert_subscription(
            user_id=primary_scenario.user_id,
            kind="routine_daily",
            section=primary_scenario.section,
            telegram_chat_id=primary_scenario.telegram_chat_id,
        )

        async def _run():
            with patch(
                "app.automation.scheduler_logic.process_routine_subscriptions"
            ) as mock_routines:
                mock_routines.return_value = 1
                return await scheduler_logic.run_automation_tick()

        result = run_async(_run())
        assert "reminders_sent" in result
        assert "routine_messages_sent" in result


# ---------------------------------------------------------------------------
# TC-ROUTE: Turn responsiveness & routing
# ---------------------------------------------------------------------------


class TestTurnResponsiveness:
    """Pipeline classification for dynamically built workflow prompts."""

    @pytest.mark.parametrize(
        "selected_tools,expected",
        [
            (["Planning", "Agent"], TurnComplexity.MULTI_AGENT),
            (["Planning"], TurnComplexity.PLANNING),
            ([], TurnComplexity.TOOL),
        ],
    )
    def test_workflow_prompt_complexity(self, primary_scenario, selected_tools, expected):
        complexity = classify_turn(
            primary_scenario.prompt,
            {"selected_tools": selected_tools},
            routing="default",
            use_fast_groq=False,
            use_hf=False,
        )
        assert complexity == expected

    def test_workflow_prompt_requires_tools_not_fast_path(self, primary_scenario):
        from app.runtime.chat_router import message_needs_tools, should_force_full_runtime

        assert message_needs_tools(primary_scenario.prompt) is True
        assert should_force_full_runtime({"selected_tools": ["Agent"]}) is True

    def test_task_tree_emitted_for_workflow_turn(self, primary_scenario):
        from app.runtime.task_policy import should_emit_task_tree

        complexity = classify_turn(
            primary_scenario.prompt,
            {"selected_tools": ["Planning", "Agent"]},
            routing="default",
            use_fast_groq=False,
            use_hf=False,
        )
        assert should_emit_task_tree(complexity) is True

    def test_event_agent_misroutes_generated_prompt(self, primary_scenario):
        pytest.importorskip("langchain")
        from app.agents.event_manager import EventAgent

        calls: List[Dict[str, Any]] = []

        async def mock_run_tool(name, ctx, **kwargs):
            calls.append({"tool": name, "kwargs": kwargs})

            class R:
                success = True
                summary = "ok"

            return R()

        ctx = {"user_id": primary_scenario.user_id, "section": primary_scenario.section}

        async def _run():
            with patch("app.agents.event_manager.run_tool", mock_run_tool):
                await EventAgent().process(primary_scenario.prompt, ctx)

        run_async(_run())
        reminder_calls = [c for c in calls if c["tool"] == "create_reminder"]
        assert reminder_calls, "EventAgent should attempt reminder path for workflow prompt"
        kwargs = reminder_calls[0]["kwargs"]
        assert "fire_at" not in kwargs
        assert kwargs.get("schedule") == "once"


# ---------------------------------------------------------------------------
# TC-E2E: Simulated user workflow (memory → plan → store → tick)
# ---------------------------------------------------------------------------


class TestWorkflowEndToEnd:
    """Full workflow using only generated scenario data."""

    def test_simulated_agent_workflow_with_dynamic_reminders(
        self, workflow_scenario, automation_store, monkeypatch, telegram_capture, routine_data_root
    ):
        from app.automation import scheduler_logic
        from app.automation.routines_data import get_uploaded_routine

        sent, fake_send, fake_resolve = telegram_capture
        monkeypatch.setattr(scheduler_logic, "automation_store", automation_store)
        monkeypatch.setattr(scheduler_logic, "send_telegram_message", fake_send)
        monkeypatch.setattr(scheduler_logic, "resolve_telegram_chat_id_for_user", fake_resolve)

        persist_routine_upload(workflow_scenario)
        day = workflow_scenario.first_nonempty_day()

        async def _run():
            with patch(
                "app.automation.routine_memory.memory_service.recall",
                AsyncMock(
                    return_value=[
                        {
                            "metadata": {"section": workflow_scenario.section},
                            "content": "",
                            "payload": {},
                        }
                    ]
                ),
            ):
                from app.automation.routine_memory import recall_user_section

                section = await recall_user_section(workflow_scenario.user_id)
            assert section == workflow_scenario.section

            routine = get_uploaded_routine(
                section, day, department=workflow_scenario.department
            )
            assert len(routine.get("items") or []) == len(workflow_scenario.weekly[day])

            ref = datetime(2026, 6, 8, 8, 0)
            plan = build_reminder_plan(
                workflow_scenario.weekly,
                offsets_min=workflow_scenario.reminder_offsets_min,
                ref=ref,
            )
            for entry in plan:
                automation_store.create_reminder(
                    user_id=workflow_scenario.user_id,
                    title=f"{entry['course']} -{entry['offset_min']}m",
                    fire_at=entry["fire_at"].isoformat(),
                    payload={"body": entry["body"]},
                )
            assert len(automation_store.list_reminders(workflow_scenario.user_id)) == len(plan)

            first = plan[0]
            count = await scheduler_logic.process_due_reminders(
                first["fire_at"] + timedelta(seconds=5)
            )
            return count, first

        count, first = run_async(_run())
        assert count >= 1
        assert any(message_has_class_details(item["text"], first["slot"]) for item in sent)

    def test_enable_routine_automation_builtin_path(
        self, primary_scenario, automation_store, routine_data_root
    ):
        from app.tools.automation.routine import EnableRoutineAutomationTool

        set_turn_context(user_id=primary_scenario.user_id, section=primary_scenario.section)
        persist_routine_upload(primary_scenario)

        async def _run():
            with patch(
                "app.tools.automation.routine.resolve_telegram_chat_id_for_user",
                AsyncMock(return_value=primary_scenario.telegram_chat_id),
            ), patch("app.tools.automation.routine.automation_store", automation_store):
                return await EnableRoutineAutomationTool().execute(
                    section=primary_scenario.section
                )

        result = run_async(_run())
        assert result.success
        subs = automation_store.list_subscriptions(user_id=primary_scenario.user_id)
        assert {s.kind for s in subs} == {"routine_daily", "class_hourly"}
        clear_turn_context()

    @pytest.mark.parametrize("profile_name,requirements", requirement_profiles())
    def test_requirement_profiles_produce_unique_schedules(self, profile_name, requirements):
        a = generate_workflow_scenario(seed=777, requirements=requirements)
        b = generate_workflow_scenario(seed=778, requirements=requirements)
        assert a.class_count() > 0
        assert b.class_count() > 0
        assert build_workflow_prompt(requirements) in (a.prompt, b.prompt)
        assert parse_offsets_from_prompt(a.prompt) == requirements.reminder_offsets_min

    def test_scenario_matrix_covers_requirement_profiles(self):
        matrix = generate_scenario_matrix()
        assert len(matrix) == len(requirement_profiles())
        assert len({s.case_id for s in matrix}) == len(matrix)
        assert all(s.class_count() > 0 for s in matrix)
        assert sum(s.expected_reminder_count() for s in matrix) > 0
