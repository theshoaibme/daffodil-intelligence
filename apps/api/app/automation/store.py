"""Persistent reminders and automation subscriptions (JSON file store)."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import get_settings


@dataclass
class ReminderRecord:
    id: str
    user_id: int
    title: str
    fire_at: str  # ISO datetime
    repeat: str = "once"  # once | daily | weekly
    channel: str = "telegram"  # telegram | in_app
    payload: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AutomationSubscription:
    id: str
    user_id: int
    kind: str  # routine_daily | class_hourly
    section: str = "64_I"
    telegram_chat_id: Optional[int] = None
    active: bool = True
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HookRecord:
    """Event-triggered automation: when `event` happens, run `action`."""

    id: str
    user_id: int
    name: str
    event: str  # on_login | on_keyword | on_schedule
    action: str  # prompt | message | agent
    payload: Dict[str, Any] = field(default_factory=dict)
    # payload keys: text, agent_id, keyword, hour (on_schedule)
    active: bool = True
    created_at: str = ""
    last_fired_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PersonalRoutineRecord:
    id: str
    user_id: int
    name: str
    schedule: str
    tasks: List[str] = field(default_factory=list)
    active: bool = True
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoopRecord:
    """Recurring prompt/command run on a fixed interval."""

    id: str
    user_id: int
    name: str
    prompt: str
    interval_minutes: int = 60
    agent_id: str = ""
    channel: str = "telegram"
    active: bool = True
    created_at: str = ""
    last_run_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutomationStore:
    def __init__(self, path: Optional[Path] = None):
        settings = get_settings()
        base = Path(settings.ANTIGRAVITY_SAVE_DIR)
        base.mkdir(parents=True, exist_ok=True)
        self._path = path or (base / "automation_store.json")
        self._lock = threading.Lock()
        self._reminders: Dict[str, ReminderRecord] = {}
        self._subscriptions: Dict[str, AutomationSubscription] = {}
        self._hooks: Dict[str, HookRecord] = {}
        self._loops: Dict[str, LoopRecord] = {}
        self._personal_routines: Dict[str, PersonalRoutineRecord] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                for r in raw.get("reminders", []):
                    rec = ReminderRecord(**r)
                    self._reminders[rec.id] = rec
                for s in raw.get("subscriptions", []):
                    sub = AutomationSubscription(**s)
                    self._subscriptions[sub.id] = sub
                for h in raw.get("hooks", []):
                    hook = HookRecord(**h)
                    self._hooks[hook.id] = hook
                for lp in raw.get("loops", []):
                    loop = LoopRecord(**lp)
                    self._loops[loop.id] = loop
                for pr in raw.get("personal_routines", []):
                    rec = PersonalRoutineRecord(**pr)
                    self._personal_routines[rec.id] = rec
            except Exception:
                self._reminders = {}
                self._subscriptions = {}
                self._hooks = {}
                self._loops = {}
                self._personal_routines = {}
        self._loaded = True

    def _save(self) -> None:
        payload = {
            "reminders": [r.to_dict() for r in self._reminders.values()],
            "subscriptions": [s.to_dict() for s in self._subscriptions.values()],
            "hooks": [h.to_dict() for h in self._hooks.values()],
            "loops": [lp.to_dict() for lp in self._loops.values()],
            "personal_routines": [r.to_dict() for r in self._personal_routines.values()],
        }
        self._path.write_text(json.dumps(payload, indent=2), "utf-8")

    def create_personal_routine(
        self,
        *,
        user_id: int,
        name: str,
        schedule: str,
        tasks: Optional[List[str]] = None,
    ) -> PersonalRoutineRecord:
        with self._lock:
            self._load()
            rec = PersonalRoutineRecord(
                id=str(uuid.uuid4())[:12],
                user_id=user_id,
                name=name.strip(),
                schedule=schedule.strip(),
                tasks=list(tasks or []),
                created_at=datetime.utcnow().isoformat(),
            )
            self._personal_routines[rec.id] = rec
            self._save()
            return rec

    def list_personal_routines(self, user_id: int, active_only: bool = True) -> List[PersonalRoutineRecord]:
        with self._lock:
            self._load()
            items = [r for r in self._personal_routines.values() if r.user_id == user_id]
            if active_only:
                items = [r for r in items if r.active]
            return sorted(items, key=lambda r: r.created_at)

    def delete_personal_routine(self, user_id: int, routine_id: str) -> bool:
        with self._lock:
            self._load()
            rec = self._personal_routines.get(routine_id)
            if not rec or rec.user_id != user_id:
                return False
            rec.active = False
            self._save()
            return True

    def create_reminder(
        self,
        *,
        user_id: int,
        title: str,
        fire_at: str,
        repeat: str = "once",
        channel: str = "telegram",
        payload: Optional[Dict[str, Any]] = None,
    ) -> ReminderRecord:
        with self._lock:
            self._load()
            rec = ReminderRecord(
                id=str(uuid.uuid4())[:12],
                user_id=user_id,
                title=title,
                fire_at=fire_at,
                repeat=repeat,
                channel=channel,
                payload=payload or {},
                created_at=datetime.utcnow().isoformat(),
            )
            self._reminders[rec.id] = rec
            self._save()
            return rec

    def list_reminders(self, user_id: int, active_only: bool = True) -> List[ReminderRecord]:
        with self._lock:
            self._load()
            items = [r for r in self._reminders.values() if r.user_id == user_id]
            if active_only:
                items = [r for r in items if r.active]
            return sorted(items, key=lambda r: r.fire_at)

    def delete_reminder(self, user_id: int, reminder_id: str) -> bool:
        with self._lock:
            self._load()
            rec = self._reminders.get(reminder_id)
            if not rec or rec.user_id != user_id:
                return False
            rec.active = False
            self._save()
            return True

    def due_reminders(self, now: Optional[datetime] = None) -> List[ReminderRecord]:
        now = now or datetime.utcnow()
        with self._lock:
            self._load()
            due: List[ReminderRecord] = []
            for rec in self._reminders.values():
                if not rec.active:
                    continue
                try:
                    fire = datetime.fromisoformat(rec.fire_at.replace("Z", ""))
                except ValueError:
                    continue
                if fire <= now:
                    due.append(rec)
            return due

    def mark_reminder_sent(self, reminder_id: str) -> None:
        with self._lock:
            self._load()
            rec = self._reminders.get(reminder_id)
            if not rec:
                return
            if rec.repeat == "once":
                rec.active = False
            self._save()

    def upsert_subscription(
        self,
        *,
        user_id: int,
        kind: str,
        section: str = "64_I",
        telegram_chat_id: Optional[int] = None,
    ) -> AutomationSubscription:
        with self._lock:
            self._load()
            for sub in self._subscriptions.values():
                if sub.user_id == user_id and sub.kind == kind and sub.active:
                    sub.section = section
                    if telegram_chat_id:
                        sub.telegram_chat_id = telegram_chat_id
                    self._save()
                    return sub
            sub = AutomationSubscription(
                id=str(uuid.uuid4())[:12],
                user_id=user_id,
                kind=kind,
                section=section,
                telegram_chat_id=telegram_chat_id,
                created_at=datetime.utcnow().isoformat(),
            )
            self._subscriptions[sub.id] = sub
            self._save()
            return sub

    def list_subscriptions(self, user_id: Optional[int] = None) -> List[AutomationSubscription]:
        with self._lock:
            self._load()
            items = [s for s in self._subscriptions.values() if s.active]
            if user_id is not None:
                items = [s for s in items if s.user_id == user_id]
            return items

    # --- Hooks (event triggers) ---

    def create_hook(
        self,
        *,
        user_id: int,
        name: str,
        event: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> HookRecord:
        with self._lock:
            self._load()
            hook = HookRecord(
                id=str(uuid.uuid4())[:12],
                user_id=user_id,
                name=name,
                event=event,
                action=action,
                payload=payload or {},
                created_at=datetime.utcnow().isoformat(),
            )
            self._hooks[hook.id] = hook
            self._save()
            return hook

    def list_hooks(self, user_id: Optional[int] = None, active_only: bool = True) -> List[HookRecord]:
        with self._lock:
            self._load()
            items = list(self._hooks.values())
            if active_only:
                items = [h for h in items if h.active]
            if user_id is not None:
                items = [h for h in items if h.user_id == user_id]
            return sorted(items, key=lambda h: h.created_at)

    def hooks_for_event(self, event: str, user_id: Optional[int] = None) -> List[HookRecord]:
        return [h for h in self.list_hooks(user_id=user_id) if h.event == event]

    def delete_hook(self, user_id: int, hook_id: str) -> bool:
        with self._lock:
            self._load()
            hook = self._hooks.get(hook_id)
            if not hook or hook.user_id != user_id:
                return False
            hook.active = False
            self._save()
            return True

    def mark_hook_fired(self, hook_id: str) -> None:
        with self._lock:
            self._load()
            hook = self._hooks.get(hook_id)
            if hook:
                hook.last_fired_at = datetime.utcnow().isoformat()
                self._save()

    # --- Loops (recurring prompts) ---

    def create_loop(
        self,
        *,
        user_id: int,
        name: str,
        prompt: str,
        interval_minutes: int = 60,
        agent_id: str = "",
        channel: str = "telegram",
    ) -> LoopRecord:
        with self._lock:
            self._load()
            loop = LoopRecord(
                id=str(uuid.uuid4())[:12],
                user_id=user_id,
                name=name,
                prompt=prompt,
                interval_minutes=max(1, int(interval_minutes)),
                agent_id=agent_id,
                channel=channel,
                created_at=datetime.utcnow().isoformat(),
            )
            self._loops[loop.id] = loop
            self._save()
            return loop

    def list_loops(self, user_id: Optional[int] = None, active_only: bool = True) -> List[LoopRecord]:
        with self._lock:
            self._load()
            items = list(self._loops.values())
            if active_only:
                items = [lp for lp in items if lp.active]
            if user_id is not None:
                items = [lp for lp in items if lp.user_id == user_id]
            return sorted(items, key=lambda lp: lp.created_at)

    def delete_loop(self, user_id: int, loop_id: str) -> bool:
        with self._lock:
            self._load()
            loop = self._loops.get(loop_id)
            if not loop or loop.user_id != user_id:
                return False
            loop.active = False
            self._save()
            return True

    def due_loops(self, now: Optional[datetime] = None) -> List[LoopRecord]:
        now = now or datetime.utcnow()
        with self._lock:
            self._load()
            due: List[LoopRecord] = []
            for loop in self._loops.values():
                if not loop.active:
                    continue
                if not loop.last_run_at:
                    due.append(loop)
                    continue
                try:
                    last = datetime.fromisoformat(loop.last_run_at.replace("Z", ""))
                except ValueError:
                    due.append(loop)
                    continue
                if (now - last) >= timedelta(minutes=loop.interval_minutes):
                    due.append(loop)
            return due

    def mark_loop_run(self, loop_id: str, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        with self._lock:
            self._load()
            loop = self._loops.get(loop_id)
            if loop:
                loop.last_run_at = now.isoformat()
                self._save()


automation_store = AutomationStore()
