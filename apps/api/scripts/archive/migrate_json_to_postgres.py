#!/usr/bin/env python3
"""One-time idempotent backfill from JSON files into PostgreSQL hub tables."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import get_settings
from app.core.database import Base, get_engine, get_session_maker
from app.models import hub  # noqa: F401
from app.models import user  # noqa: F401
from app.skills.models import AgentProfile, GlobalAgentConfig
from app.skills.repository import HubRepository

logger = logging.getLogger(__name__)
DATA_DIR = API_ROOT / "data" / "examples"


def _load_json(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception as e:
        logger.warning("Could not read %s: %s", path, e)
        return {}


async def migrate() -> dict:
    counts = {
        "skills": 0,
        "rulesets": 0,
        "custom_agents": 0,
        "agent_profiles": 0,
        "global_config": 0,
    }

    engine = get_engine()
    if engine is None:
        raise RuntimeError("Database engine unavailable")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = get_session_maker()
    if session_maker is None:
        raise RuntimeError("Session maker unavailable")

    async with session_maker() as session:
        repo = HubRepository(session)

        skills_raw = _load_json("skills.json")
        for sid, data in skills_raw.items():
            existing = await repo.get_skill(sid)
            if existing:
                continue
            created_at = data.get("created_at")
            await repo.create_skill(
                name=data["name"],
                description=data.get("description", ""),
                content=data.get("content", ""),
                skill_id=sid,
                tool_names=data.get("tool_names") or [],
                source=data.get("source", "manual"),
                recording_name=data.get("recording_name"),
                tags=data.get("tags") or [],
                created_by=data.get("created_by", 0),
                is_public=data.get("is_public", True),
            )
            if created_at:
                await repo.update_skill(sid, usage_count=data.get("usage_count", 0))
            counts["skills"] += 1

        rulesets_raw = _load_json("rulesets.json")
        for rid, data in rulesets_raw.items():
            if await repo.get_ruleset(rid):
                continue
            await repo.create_ruleset(
                name=data["name"],
                description=data.get("description", ""),
                rules=data.get("rules") or [],
                ruleset_id=rid,
                created_by=data.get("created_by", 0),
                is_public=data.get("is_public", True),
            )
            counts["rulesets"] += 1

        agents_raw = _load_json("custom_agents.json")
        for aid, data in agents_raw.items():
            if await repo.get_custom_agent(aid):
                continue
            from app.models.hub import CustomAgent

            row = CustomAgent(
                id=aid,
                name=data["name"],
                description=data.get("description", ""),
                agent_type=data.get("agent_type", "custom"),
                personality=data.get("personality") or {},
                capabilities=data.get("capabilities") or [],
                system_prompt=data.get("system_prompt", ""),
                created_by=data.get("created_by"),
                is_public=data.get("is_public", False),
                usage_count=data.get("usage_count", 0),
                rating=data.get("rating", 0.0),
            )
            await repo.create_custom_agent(row)
            counts["custom_agents"] += 1

        profiles_raw = _load_json("agent_profiles.json")
        for agent_id, data in profiles_raw.items():
            profile = AgentProfile(
                agent_id=agent_id,
                ruleset_ids=data.get("ruleset_ids") or [],
                skill_ids=data.get("skill_ids") or [],
                extra_system=data.get("extra_system", ""),
            )
            await repo.upsert_agent_profile(profile)
            counts["agent_profiles"] += 1

        global_raw = _load_json("global_agent_config.json")
        if global_raw:
            cfg = GlobalAgentConfig(
                ruleset_ids=global_raw.get("ruleset_ids") or [],
                skill_ids=global_raw.get("skill_ids") or [],
                extra_system=global_raw.get("extra_system", ""),
                default_agent_id=global_raw.get("default_agent_id", "main"),
            )
            await repo.save_global_config(cfg)
            counts["global_config"] = 1

    logger.info("Migration complete: %s", counts)
    return counts


def main():
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    logger.info("Backfill target: %s", settings.DATABASE_URL)
    counts = asyncio.run(migrate())
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
