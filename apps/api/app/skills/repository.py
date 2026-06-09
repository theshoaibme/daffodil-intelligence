"""Async PostgreSQL repository for skills hub, rulesets, and agent configuration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import hub as hub_models
from .models import AgentProfile, GlobalAgentConfig, Ruleset, Skill


def _dt_to_ts(dt: Optional[datetime]) -> float:
    if dt is None:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _skill_to_pydantic(row: hub_models.Skill) -> Skill:
    return Skill(
        id=str(row.id),
        name=row.name,
        description=row.description or "",
        content=row.content or "",
        tool_names=list(row.tool_names or []),
        source=row.source or "manual",
        recording_name=row.recording_name,
        tags=list(row.tags or []),
        created_by=row.created_by or 0,
        is_public=bool(row.is_public),
        usage_count=row.usage_count or 0,
        created_at=_dt_to_ts(row.created_at),
    )


def _ruleset_to_pydantic(row: hub_models.Ruleset) -> Ruleset:
    return Ruleset(
        id=str(row.id),
        name=row.name,
        description=row.description or "",
        rules=list(row.rules or []),
        created_by=row.created_by or 0,
        is_public=bool(row.is_public),
        created_at=_dt_to_ts(row.created_at),
    )


class HubRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Skills ---

    async def get_skill(self, skill_id: str) -> Optional[Skill]:
        row = await self.session.get(hub_models.Skill, skill_id)
        return _skill_to_pydantic(row) if row else None

    async def list_skills(
        self,
        *,
        user_id: Optional[int] = None,
        public_only: bool = False,
        limit: int = 100,
        offset: int = 0,
        tag: Optional[str] = None,
        source: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[Skill], int]:
        stmt = select(hub_models.Skill)
        count_stmt = select(func.count()).select_from(hub_models.Skill)

        filters = []
        if public_only:
            filters.append(hub_models.Skill.is_public.is_(True))
        elif user_id is not None:
            filters.append(
                or_(
                    hub_models.Skill.is_public.is_(True),
                    hub_models.Skill.created_by == user_id,
                )
            )
        if tag:
            filters.append(hub_models.Skill.tags.contains([tag]))
        if source:
            filters.append(hub_models.Skill.source == source)
        if q:
            pattern = f"%{q.strip()}%"
            filters.append(
                or_(
                    hub_models.Skill.name.ilike(pattern),
                    hub_models.Skill.description.ilike(pattern),
                )
            )

        for f in filters:
            stmt = stmt.where(f)
            count_stmt = count_stmt.where(f)

        stmt = stmt.order_by(hub_models.Skill.created_at.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return [_skill_to_pydantic(r) for r in rows], int(total)

    async def create_skill(
        self,
        name: str,
        description: str,
        content: str,
        *,
        skill_id: Optional[str] = None,
        tool_names: Optional[List[str]] = None,
        source: str = "manual",
        recording_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: int = 0,
        is_public: bool = True,
    ) -> Skill:
        row = hub_models.Skill(
            id=skill_id or str(uuid.uuid4()),
            name=name,
            description=description,
            content=content,
            tool_names=tool_names or [],
            source=source,
            recording_name=recording_name,
            tags=tags or [],
            created_by=created_by or None,
            is_public=is_public,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return _skill_to_pydantic(row)

    async def update_skill(self, skill_id: str, **fields) -> Optional[Skill]:
        row = await self.session.get(hub_models.Skill, skill_id)
        if not row:
            return None
        for key, val in fields.items():
            if val is not None and hasattr(row, key):
                setattr(row, key, val)
        await self.session.commit()
        await self.session.refresh(row)
        return _skill_to_pydantic(row)

    async def delete_skill(self, skill_id: str) -> bool:
        row = await self.session.get(hub_models.Skill, skill_id)
        if not row:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True

    async def increment_skill_usage(self, skill_id: str) -> None:
        await self.session.execute(
            update(hub_models.Skill)
            .where(hub_models.Skill.id == skill_id)
            .values(usage_count=hub_models.Skill.usage_count + 1)
        )
        await self.session.commit()

    async def skill_stats(self, user_id: Optional[int] = None) -> dict:
        skills, total = await self.list_skills(user_id=user_id, limit=10000, offset=0)
        return {
            "count": total,
            "public_count": sum(1 for s in skills if s.is_public),
            "copycat_count": sum(1 for s in skills if s.source == "copycat"),
        }

    # --- Rulesets ---

    async def get_ruleset(self, ruleset_id: str) -> Optional[Ruleset]:
        row = await self.session.get(hub_models.Ruleset, ruleset_id)
        return _ruleset_to_pydantic(row) if row else None

    async def list_rulesets(
        self,
        *,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Ruleset], int]:
        stmt = select(hub_models.Ruleset)
        count_stmt = select(func.count()).select_from(hub_models.Ruleset)
        if user_id is not None:
            filt = or_(
                hub_models.Ruleset.is_public.is_(True),
                hub_models.Ruleset.created_by == user_id,
            )
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        stmt = stmt.order_by(hub_models.Ruleset.created_at.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return [_ruleset_to_pydantic(r) for r in rows], int(total)

    async def create_ruleset(
        self,
        name: str,
        description: str,
        rules: List[str],
        *,
        ruleset_id: Optional[str] = None,
        created_by: int = 0,
        is_public: bool = True,
    ) -> Ruleset:
        row = hub_models.Ruleset(
            id=ruleset_id or str(uuid.uuid4()),
            name=name,
            description=description,
            rules=rules,
            created_by=created_by or None,
            is_public=is_public,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return _ruleset_to_pydantic(row)

    async def update_ruleset(self, ruleset_id: str, **fields) -> Optional[Ruleset]:
        row = await self.session.get(hub_models.Ruleset, ruleset_id)
        if not row:
            return None
        for key, val in fields.items():
            if val is not None and hasattr(row, key):
                setattr(row, key, val)
        await self.session.commit()
        await self.session.refresh(row)
        return _ruleset_to_pydantic(row)

    async def delete_ruleset(self, ruleset_id: str) -> bool:
        row = await self.session.get(hub_models.Ruleset, ruleset_id)
        if not row:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True

    # --- Global config ---

    async def _ensure_global_config(self) -> hub_models.GlobalAgentConfig:
        row = await self.session.get(hub_models.GlobalAgentConfig, 1)
        if row is None:
            row = hub_models.GlobalAgentConfig(id=1, extra_system="", default_agent_id="main")
            self.session.add(row)
            await self.session.commit()
            await self.session.refresh(row)
        return row

    async def _link_ids(self, model, id_col) -> List[str]:
        stmt = select(model).order_by(model.sort_order)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [str(getattr(r, id_col)) for r in rows]

    async def get_global_config(self) -> GlobalAgentConfig:
        await self._ensure_global_config()
        row = await self.session.get(hub_models.GlobalAgentConfig, 1)
        skill_ids = await self._link_ids(hub_models.GlobalSkillLink, "skill_id")
        ruleset_ids = await self._link_ids(hub_models.GlobalRulesetLink, "ruleset_id")
        return GlobalAgentConfig(
            ruleset_ids=ruleset_ids,
            skill_ids=skill_ids,
            extra_system=row.extra_system or "",
            default_agent_id=row.default_agent_id or "main",
        )

    async def save_global_config(self, config: GlobalAgentConfig) -> GlobalAgentConfig:
        row = await self._ensure_global_config()
        row.extra_system = config.extra_system
        row.default_agent_id = config.default_agent_id or "main"
        await self.session.commit()
        await self.set_global_links(config.skill_ids, config.ruleset_ids)
        return await self.get_global_config()

    async def patch_global_config(self, **fields) -> GlobalAgentConfig:
        cfg = await self.get_global_config()
        data = cfg.model_dump()
        data.update({k: v for k, v in fields.items() if v is not None})
        return await self.save_global_config(GlobalAgentConfig(**data))

    async def set_global_links(
        self,
        skill_ids: Optional[List[str]] = None,
        ruleset_ids: Optional[List[str]] = None,
    ) -> GlobalAgentConfig:
        if skill_ids is not None:
            await self.session.execute(delete(hub_models.GlobalSkillLink))
            for i, sid in enumerate(skill_ids):
                self.session.add(hub_models.GlobalSkillLink(skill_id=sid, sort_order=i))
        if ruleset_ids is not None:
            await self.session.execute(delete(hub_models.GlobalRulesetLink))
            for i, rid in enumerate(ruleset_ids):
                self.session.add(hub_models.GlobalRulesetLink(ruleset_id=rid, sort_order=i))
        await self.session.commit()
        return await self.get_global_config()

    # --- Agent profiles ---

    async def _agent_link_ids(self, agent_id: str) -> Tuple[List[str], List[str]]:
        sk_stmt = (
            select(hub_models.AgentSkillLink)
            .where(hub_models.AgentSkillLink.agent_id == agent_id)
            .order_by(hub_models.AgentSkillLink.sort_order)
        )
        rs_stmt = (
            select(hub_models.AgentRulesetLink)
            .where(hub_models.AgentRulesetLink.agent_id == agent_id)
            .order_by(hub_models.AgentRulesetLink.sort_order)
        )
        skill_ids = [str(r.skill_id) for r in (await self.session.execute(sk_stmt)).scalars()]
        ruleset_ids = [str(r.ruleset_id) for r in (await self.session.execute(rs_stmt)).scalars()]
        return skill_ids, ruleset_ids

    async def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        row = await self.session.get(hub_models.AgentProfile, agent_id)
        skill_ids, ruleset_ids = await self._agent_link_ids(agent_id)
        if row is None and not skill_ids and not ruleset_ids:
            return None
        return AgentProfile(
            agent_id=agent_id,
            ruleset_ids=ruleset_ids,
            skill_ids=skill_ids,
            extra_system=row.extra_system if row else "",
        )

    async def upsert_agent_profile(self, profile: AgentProfile) -> AgentProfile:
        row = await self.session.get(hub_models.AgentProfile, profile.agent_id)
        if row is None:
            row = hub_models.AgentProfile(
                agent_id=profile.agent_id,
                extra_system=profile.extra_system or "",
            )
            self.session.add(row)
        else:
            row.extra_system = profile.extra_system or ""
        await self.session.commit()
        await self.set_agent_links(profile.agent_id, profile.skill_ids, profile.ruleset_ids)
        result = await self.get_agent_profile(profile.agent_id)
        return result or profile

    async def set_agent_links(
        self,
        agent_id: str,
        skill_ids: Optional[List[str]] = None,
        ruleset_ids: Optional[List[str]] = None,
    ) -> AgentProfile:
        if skill_ids is not None:
            await self.session.execute(
                delete(hub_models.AgentSkillLink).where(
                    hub_models.AgentSkillLink.agent_id == agent_id
                )
            )
            for i, sid in enumerate(skill_ids):
                self.session.add(
                    hub_models.AgentSkillLink(agent_id=agent_id, skill_id=sid, sort_order=i)
                )
        if ruleset_ids is not None:
            await self.session.execute(
                delete(hub_models.AgentRulesetLink).where(
                    hub_models.AgentRulesetLink.agent_id == agent_id
                )
            )
            for i, rid in enumerate(ruleset_ids):
                self.session.add(
                    hub_models.AgentRulesetLink(
                        agent_id=agent_id, ruleset_id=rid, sort_order=i
                    )
                )
        await self.session.commit()
        existing = await self.get_agent_profile(agent_id)
        return existing or AgentProfile(agent_id=agent_id)

    async def validate_skill_ids(self, skill_ids: List[str]) -> List[str]:
        missing = []
        for sid in skill_ids:
            if not await self.get_skill(sid):
                missing.append(sid)
        return missing

    async def validate_ruleset_ids(self, ruleset_ids: List[str]) -> List[str]:
        missing = []
        for rid in ruleset_ids:
            if not await self.get_ruleset(rid):
                missing.append(rid)
        return missing

    # --- Custom agents ---

    async def get_custom_agent(self, agent_id: str):
        return await self.session.get(hub_models.CustomAgent, agent_id)

    async def list_custom_agents(
        self,
        *,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        stmt = select(hub_models.CustomAgent)
        count_stmt = select(func.count()).select_from(hub_models.CustomAgent)
        if user_id is not None:
            filt = or_(
                hub_models.CustomAgent.is_public.is_(True),
                hub_models.CustomAgent.created_by == user_id,
            )
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        stmt = stmt.order_by(hub_models.CustomAgent.created_at.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return rows, int(total)

    async def create_custom_agent(self, row: hub_models.CustomAgent):
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def update_custom_agent(self, agent_id: str, **fields):
        row = await self.session.get(hub_models.CustomAgent, agent_id)
        if not row:
            return None
        for key, val in fields.items():
            if val is not None and hasattr(row, key):
                setattr(row, key, val)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def delete_custom_agent(self, agent_id: str) -> bool:
        row = await self.session.get(hub_models.CustomAgent, agent_id)
        if not row:
            return False
        profile = await self.session.get(hub_models.AgentProfile, agent_id)
        if profile:
            await self.session.delete(profile)
        await self.session.delete(row)
        await self.session.commit()
        return True

    async def increment_agent_usage(self, agent_id: str) -> Optional[int]:
        row = await self.session.get(hub_models.CustomAgent, agent_id)
        if not row:
            return None
        row.usage_count = (row.usage_count or 0) + 1
        await self.session.commit()
        return row.usage_count

    async def rate_agent(self, agent_id: str, rating: float) -> Optional[float]:
        row = await self.session.get(hub_models.CustomAgent, agent_id)
        if not row:
            return None
        count = row.usage_count or 0
        row.rating = (row.rating * count + rating) / (count + 1)
        await self.session.commit()
        return round(row.rating, 2)

    async def count_agent_skills(self, agent_id: str) -> int:
        stmt = select(func.count()).select_from(hub_models.AgentSkillLink).where(
            hub_models.AgentSkillLink.agent_id == agent_id
        )
        return int((await self.session.execute(stmt)).scalar_one())


async def get_hub_repository(session: AsyncSession) -> HubRepository:
    return HubRepository(session)
