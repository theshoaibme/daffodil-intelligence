"""PostgreSQL models for skills hub, rulesets, custom agents, and junction links."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func, text

from ..core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    content = Column(Text, nullable=False, default="")
    tool_names = Column(JSONB, nullable=False, server_default="[]")
    source = Column(String(32), nullable=False, default="manual")
    recording_name = Column(String(255), nullable=True)
    tags = Column(JSONB, nullable=False, server_default="[]")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, nullable=False, default=True)
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_skills_created_by_created_at", "created_by", "created_at"),
        Index("ix_skills_is_public_created_at", "is_public", "created_at"),
        Index("ix_skills_source", "source"),
        Index("ix_skills_tags_gin", "tags", postgresql_using="gin"),
        Index(
            "ix_skills_search",
            text("to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))"),
            postgresql_using="gin",
        ),
    )


class Ruleset(Base):
    __tablename__ = "rulesets"

    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    rules = Column(JSONB, nullable=False, server_default="[]")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_rulesets_created_by_created_at", "created_by", "created_at"),
        Index("ix_rulesets_is_public_created_at", "is_public", "created_at"),
    )


class CustomAgent(Base):
    __tablename__ = "custom_agents"

    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    agent_type = Column(String(64), nullable=False, default="custom")
    personality = Column(JSONB, nullable=False, server_default="{}")
    capabilities = Column(JSONB, nullable=False, server_default="[]")
    system_prompt = Column(Text, nullable=False, default="")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)
    usage_count = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_custom_agents_created_by_created_at", "created_by", "created_at"),
        Index("ix_custom_agents_is_public_usage", "is_public", "usage_count"),
        Index("ix_custom_agents_agent_type", "agent_type"),
    )


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    agent_id = Column(String(64), primary_key=True)
    extra_system = Column(Text, nullable=False, default="")


class GlobalAgentConfig(Base):
    __tablename__ = "global_agent_config"

    id = Column(Integer, primary_key=True, default=1)
    extra_system = Column(Text, nullable=False, default="")
    default_agent_id = Column(String(64), nullable=False, default="main")


class AgentSkillLink(Base):
    __tablename__ = "agent_skill_links"

    agent_id = Column(String(64), primary_key=True)
    skill_id = Column(
        UUID(as_uuid=False),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_agent_skill_links_skill_id", "skill_id"),)


class AgentRulesetLink(Base):
    __tablename__ = "agent_ruleset_links"

    agent_id = Column(String(64), primary_key=True)
    ruleset_id = Column(
        UUID(as_uuid=False),
        ForeignKey("rulesets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_agent_ruleset_links_ruleset_id", "ruleset_id"),)


class GlobalSkillLink(Base):
    __tablename__ = "global_skill_links"

    skill_id = Column(
        UUID(as_uuid=False),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order = Column(Integer, nullable=False, default=0)


class GlobalRulesetLink(Base):
    __tablename__ = "global_ruleset_links"

    ruleset_id = Column(
        UUID(as_uuid=False),
        ForeignKey("rulesets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order = Column(Integer, nullable=False, default=0)
