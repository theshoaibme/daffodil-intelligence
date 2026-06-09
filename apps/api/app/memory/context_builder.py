"""Snapshot runtime config and build recall context for agent turns."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..core.config import get_settings
from ..skills.resolver import RuntimeConfig, resolve_runtime_config
from ..tools.registry import get_registry
from .pg_user import pg_memory_user_id
from .repository import MemoryRepository
from .types import CONFIG_TYPES, ROOT_AGENT_ID, compute_content_hash

logger = logging.getLogger(__name__)
settings = get_settings()


async def _get_mcp_servers() -> List[Dict[str, Any]]:
    try:
        from ..core.health_checks import _check_mcp

        status = _check_mcp()
        servers = status.get("servers") or []
        return [
            {
                "server_name": name,
                "transport": status.get("transport", "stdio"),
                "tools": [],
            }
            for name in servers
        ]
    except Exception as e:
        logger.debug("MCP status unavailable: %s", e)
        return []


class MemoryContextBuilder:
    def __init__(self, repo: MemoryRepository):
        self.repo = repo

    async def snapshot_runtime_context(
        self,
        user_id: int,
        agent_id: str,
        cfg: RuntimeConfig,
    ) -> None:
        """Upsert config snapshots when content hash changes."""
        if cfg.extra_system.strip():
            await self.repo.upsert(
                user_id=user_id,
                agent_id=agent_id,
                content=cfg.extra_system.strip()[:4000],
                memory_type="system_prompt",
                visibility="agent_tree",
                source="system",
                payload={
                    "agent_id": agent_id,
                    "prompt_text": cfg.extra_system.strip(),
                    "skill_ids": cfg.skill_ids,
                    "ruleset_ids": cfg.ruleset_ids,
                },
                content_hash=compute_content_hash(
                    "system_prompt", agent_id, cfg.extra_system.strip()[:4000]
                ),
            )

        from ..core.database import get_session_maker
        from ..skills.repository import HubRepository

        session_maker = get_session_maker()
        if session_maker:
            async with session_maker() as session:
                hub = HubRepository(session)
                for sk_id in cfg.skill_ids:
                    sk = await hub.get_skill(sk_id)
                    if not sk:
                        continue
                    content = f"Skill: {sk.name}\n{sk.content.strip()[:2000]}"
                    await self.repo.upsert(
                        user_id=user_id,
                        agent_id=agent_id,
                        content=content,
                        memory_type="skill",
                        visibility="agent_tree",
                        source="system",
                        payload={
                            "skill_id": sk.id,
                            "name": sk.name,
                            "content": sk.content,
                            "tool_names": sk.tool_names,
                        },
                        metadata={"skill_ids": [sk.id]},
                    )

                for rs_id in cfg.ruleset_ids:
                    rs = await hub.get_ruleset(rs_id)
                    if not rs:
                        continue
                    content = f"Ruleset: {rs.name}\n" + "\n".join(rs.rules[:20])
                    await self.repo.upsert(
                        user_id=user_id,
                        agent_id=agent_id,
                        content=content,
                        memory_type="ruleset",
                        visibility="agent_tree",
                        source="system",
                        payload={
                            "ruleset_id": rs.id,
                            "name": rs.name,
                            "rules": rs.rules,
                        },
                        metadata={"ruleset_ids": [rs.id]},
                    )

                custom = await hub.get_custom_agent(agent_id)
                if custom:
                    await self.repo.upsert(
                        user_id=user_id,
                        agent_id=agent_id,
                        content=f"Agent: {custom.get('name', agent_id)}",
                        memory_type="agent_config",
                        visibility="agent_tree",
                        source="system",
                        payload={
                            "name": custom.get("name"),
                            "description": custom.get("description"),
                            "capabilities": custom.get("capabilities", []),
                            "system_prompt": custom.get("system_prompt"),
                        },
                    )

        registry = get_registry()
        for schema in registry.list_all():
            content = f"{schema['name']}: {schema.get('description', '')}"
            payload = {
                "tool_name": schema["name"],
                "description": schema.get("description", ""),
                "parameters": schema.get("inputSchema", {}),
                "category": schema.get("category", "general"),
            }
            await self.repo.upsert(
                user_id=user_id,
                agent_id=agent_id,
                content=content,
                memory_type="tool_definition",
                visibility="agent_tree",
                source="system",
                payload=payload,
            )

        for server in await _get_mcp_servers():
            name = server["server_name"]
            content = f"MCP server: {name}"
            await self.repo.upsert(
                user_id=user_id,
                agent_id=agent_id,
                content=content,
                memory_type="mcp_server",
                visibility="agent_tree",
                source="system",
                payload=server,
            )

    async def build_recall_context(
        self,
        user_id: int,
        agent_id: str,
        message: str,
        *,
        chat_id: Optional[Any] = None,
        k: int = 10,
    ) -> str:
        """Build extra_system block from recalled memories."""
        is_root = agent_id == ROOT_AGENT_ID
        recall_k = k if is_root else min(k, 5)

        fact_types = ["fact", "preference", "episode"]
        facts = await self.repo.recall(
            message,
            user_id,
            caller_agent_id=agent_id,
            memory_types=fact_types,
            k=recall_k,
        )

        conv_types = ["conversation_summary", "subagent_result"]
        conv = await self.repo.recall(
            message,
            user_id,
            caller_agent_id=agent_id,
            memory_types=conv_types,
            chat_id=None if is_root else chat_id,
            k=3,
        )

        parts: List[str] = []

        if facts:
            parts.append("## Recalled memory")
            for f in facts:
                tag = f.get("metadata", {}).get("tag") or f.get("memory_type", "fact")
                parts.append(f"- [{tag}] {f['content'][:300]}")

        if conv:
            parts.append("## Conversation context")
            for c in conv:
                cid = c.get("metadata", {}).get("chat_id", "")
                parts.append(f"- [summary][chat:{cid}] {c['content'][:300]}")

        snapshots = await self.repo.latest_config_snapshots(user_id, agent_id)
        if snapshots:
            parts.append("## Active configuration (this turn)")
            skills = [s for s in snapshots if s["memory_type"] == "skill"]
            rules = [s for s in snapshots if s["memory_type"] == "ruleset"]
            tools = [s for s in snapshots if s["memory_type"] == "tool_definition"]
            mcp = [s for s in snapshots if s["memory_type"] == "mcp_server"]

            if skills:
                names = [s["payload"].get("name", s["content"][:40]) for s in skills[:5]]
                parts.append(f"- Skills: {', '.join(names)}")
            if rules:
                names = [s["payload"].get("name", s["content"][:40]) for s in rules[:5]]
                parts.append(f"- Rules: {', '.join(names)}")
            if tools:
                names = [s["payload"].get("tool_name", s["content"][:30]) for s in tools[:8]]
                parts.append(f"- Tools: {', '.join(names)}")
            if mcp:
                names = [s["payload"].get("server_name", s["content"][:30]) for s in mcp]
                parts.append(f"- MCP: {', '.join(names)}")

        return "\n".join(parts).strip()


async def build_turn_memory_context(
    user_id: int,
    agent_id: str,
    message: str,
    *,
    chat_id: Optional[Any] = None,
    cfg: Optional[RuntimeConfig] = None,
) -> str:
    """High-level helper used by pipeline: snapshot + recall."""
    from ..core.database import get_session_maker

    if cfg is None:
        cfg = await resolve_runtime_config(agent_id=agent_id, user_id=user_id)

    pg_uid = pg_memory_user_id(user_id)
    if pg_uid is None:
        return ""

    maker = get_session_maker()
    if maker is None:
        return ""

    async with maker() as session:
        repo = MemoryRepository(session)
        builder = MemoryContextBuilder(repo)
        try:
            await builder.snapshot_runtime_context(pg_uid, agent_id, cfg)
        except Exception as e:
            logger.warning("snapshot_runtime_context failed: %s", e)
        try:
            return await builder.build_recall_context(
                pg_uid, agent_id, message, chat_id=chat_id
            )
        except Exception as e:
            logger.warning("build_recall_context failed: %s", e)
            return ""
