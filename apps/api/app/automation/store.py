"""Persistent reminders and automation subscriptions (JSON file store)."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
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


class AutomationStore:
    def __init__(self, path: Optional[Path] = None):
        settings = get_settings()
        base = Path(settings.ANTIGRAVITY_SAVE_DIR)
        base.mkdir(parents=True, exist_ok=True)
        self._path = path or (base / "automation_store.json")
        self._lock = threading.Lock()
        self._reminders: Dict[str, ReminderRecord] = {}
        self._subscriptions: Dict[str, AutomationSubscription] = {}
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
            except Exception:
                self._reminders = {}
                self._subscriptions = {}
        self._loaded = True

    def _save(self) -> None:
        payload = {
            "reminders": [r.to_dict() for r in self._reminders.values()],
            "subscriptions": [s.to_dict() for s in self._subscriptions.values()],
        }
        self._path.write_text(json.dumps(payload, indent=2), "utf-8")

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


automation_store = AutomationStore()
