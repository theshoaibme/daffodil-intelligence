"""Kit device persistence."""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from ..core.database import get_session_maker
from ..models.kit import KitAuditEvent, KitDevice, KitPairingCode


@asynccontextmanager
async def _session():
    sm = get_session_maker()
    if not sm:
        yield None
        return
    async with sm() as session:
        yield session


class KitRepository:
    async def create_pairing_code(self, user_id: int, ttl_minutes: int = 5) -> str:
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        async with _session() as session:
            if session is None:
                return code
            session.add(KitPairingCode(code=code, user_id=user_id, expires_at=expires))
            await session.commit()
        return code

    async def confirm_pairing(
        self,
        code: str,
        device_id: str,
        device_name: str = "desktop",
        allowed_roots: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        async with _session() as session:
            if session is None:
                return None
            row = await session.get(KitPairingCode, code)
            if not row or row.expires_at.replace(tzinfo=timezone.utc) < now:
                return None
            user_id = row.user_id
            device_secret = secrets.token_hex(32)
            device = KitDevice(
                id=device_id,
                user_id=user_id,
                name=device_name,
                device_secret=device_secret,
                allowed_roots=allowed_roots or [],
            )
            session.add(device)
            await session.delete(row)
            await session.commit()
            return {
                "device_id": device_id,
                "device_secret": device_secret,
                "user_id": user_id,
            }

    async def list_devices(self, user_id: int) -> List[Dict[str, Any]]:
        async with _session() as session:
            if session is None:
                return []
            result = await session.execute(
                select(KitDevice).where(KitDevice.user_id == user_id)
            )
            devices = result.scalars().all()
            return [
                {
                    "id": d.id,
                    "name": d.name,
                    "is_online": d.is_online,
                    "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                    "allowed_roots": d.allowed_roots,
                }
                for d in devices
            ]

    async def get_online_device(self, user_id: int, device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from .bridge import _connections

        async with _session() as session:
            if session is None:
                return None
            if device_id:
                d = await session.get(KitDevice, device_id)
                if d and d.user_id == user_id and d.id in _connections:
                    return {"id": d.id, "device_secret": d.device_secret, "name": d.name}
                return None
            result = await session.execute(
                select(KitDevice).where(KitDevice.user_id == user_id, KitDevice.is_online == True)  # noqa: E712
            )
            for d in result.scalars().all():
                if d.id in _connections:
                    return {"id": d.id, "device_secret": d.device_secret, "name": d.name}
            result = await session.execute(select(KitDevice).where(KitDevice.user_id == user_id))
            for d in result.scalars().all():
                if d.id in _connections:
                    return {"id": d.id, "device_secret": d.device_secret, "name": d.name}
        return None

    async def set_online(self, device_id: str, online: bool) -> None:
        async with _session() as session:
            if session is None:
                return
            await session.execute(
                update(KitDevice)
                .where(KitDevice.id == device_id)
                .values(is_online=online, last_seen_at=datetime.now(timezone.utc))
            )
            await session.commit()

    async def log_audit(
        self,
        user_id: int,
        device_id: str,
        command: str,
        payload: Optional[Dict],
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        async with _session() as session:
            if session is None:
                return
            session.add(KitAuditEvent(
                user_id=user_id,
                device_id=device_id,
                command=command,
                payload=payload,
                success=success,
                error=error,
            ))
            await session.commit()
