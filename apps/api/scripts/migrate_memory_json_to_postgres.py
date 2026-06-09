#!/usr/bin/env python3
"""Backfill memory_store.json into agent_memories table."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.core.database import get_session_maker  # noqa: E402
from app.memory.repository import MemoryRepository  # noqa: E402


async def main() -> None:
    store_path = API_ROOT / "memory_store.json"
    if not store_path.exists():
        print("No memory_store.json found, nothing to migrate.")
        return

    notes = json.loads(store_path.read_text("utf-8"))
    maker = get_session_maker()
    if maker is None:
        print("Database unavailable.")
        return

    from sqlalchemy import select
    from app.models.user import User

    migrated = 0
    skipped = 0
    async with maker() as session:
        repo = MemoryRepository(session)
        for note in notes:
            uid = int(note.get("user_id") or 0)
            text = note.get("text", "").strip()
            if not text or not uid:
                continue
            exists = await session.execute(select(User.id).where(User.id == uid))
            if exists.scalar_one_or_none() is None:
                skipped += 1
                continue
            try:
                await repo.upsert(
                    user_id=uid,
                    agent_id="main",
                    content=text,
                    memory_type="fact",
                    visibility="shared",
                    source="import",
                    metadata=note.get("metadata") or {},
                )
                migrated += 1
            except Exception as e:
                print(f"Skip note for user {uid}: {e}")
                skipped += 1

    archive = API_ROOT / "data" / "examples" / "memory_store.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(store_path.read_text("utf-8"), encoding="utf-8")
    print(f"Migrated {migrated} notes ({skipped} skipped). Archived to {archive}")


if __name__ == "__main__":
    asyncio.run(main())
