"""Hub tables for skills, rulesets, custom agents, and junction links.

Revision ID: 003_hub_tables
Revises: 002_indexes_existing
Create Date: 2026-06-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_hub_tables"
down_revision: Union[str, None] = "002_indexes_existing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("tool_names", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("source", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("recording_name", sa.String(255)),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_skills_created_by_created_at", "skills", ["created_by", "created_at"])
    op.create_index("ix_skills_is_public_created_at", "skills", ["is_public", "created_at"])
    op.create_index("ix_skills_source", "skills", ["source"])
    op.create_index("ix_skills_tags_gin", "skills", ["tags"], postgresql_using="gin")
    op.execute(
        """
        CREATE INDEX ix_skills_search ON skills USING gin (
            to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))
        )
        """
    )

    op.create_table(
        "rulesets",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("rules", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_rulesets_created_by_created_at", "rulesets", ["created_by", "created_at"])
    op.create_index("ix_rulesets_is_public_created_at", "rulesets", ["is_public", "created_at"])

    op.create_table(
        "custom_agents",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("agent_type", sa.String(64), nullable=False, server_default="custom"),
        sa.Column("personality", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_custom_agents_created_by_created_at",
        "custom_agents",
        ["created_by", "created_at"],
    )
    op.create_index(
        "ix_custom_agents_is_public_usage",
        "custom_agents",
        ["is_public", "usage_count"],
    )
    op.create_index("ix_custom_agents_agent_type", "custom_agents", ["agent_type"])

    op.create_table(
        "agent_profiles",
        sa.Column("agent_id", sa.String(64), primary_key=True),
        sa.Column("extra_system", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "global_agent_config",
        sa.Column("id", sa.Integer(), primary_key=True, server_default="1"),
        sa.Column("extra_system", sa.Text(), nullable=False, server_default=""),
        sa.Column("default_agent_id", sa.String(64), nullable=False, server_default="main"),
    )

    op.create_table(
        "agent_skill_links",
        sa.Column("agent_id", sa.String(64), primary_key=True),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_agent_skill_links_skill_id", "agent_skill_links", ["skill_id"])

    op.create_table(
        "agent_ruleset_links",
        sa.Column("agent_id", sa.String(64), primary_key=True),
        sa.Column(
            "ruleset_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("rulesets.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_agent_ruleset_links_ruleset_id", "agent_ruleset_links", ["ruleset_id"])

    op.create_table(
        "global_skill_links",
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "global_ruleset_links",
        sa.Column(
            "ruleset_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("rulesets.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        """
        INSERT INTO global_agent_config (id, extra_system, default_agent_id)
        VALUES (1, '', 'main')
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("global_ruleset_links")
    op.drop_table("global_skill_links")
    op.drop_index("ix_agent_ruleset_links_ruleset_id", table_name="agent_ruleset_links")
    op.drop_table("agent_ruleset_links")
    op.drop_index("ix_agent_skill_links_skill_id", table_name="agent_skill_links")
    op.drop_table("agent_skill_links")
    op.drop_table("global_agent_config")
    op.drop_table("agent_profiles")
    op.drop_index("ix_custom_agents_agent_type", table_name="custom_agents")
    op.drop_index("ix_custom_agents_is_public_usage", table_name="custom_agents")
    op.drop_index("ix_custom_agents_created_by_created_at", table_name="custom_agents")
    op.drop_table("custom_agents")
    op.drop_index("ix_rulesets_is_public_created_at", table_name="rulesets")
    op.drop_index("ix_rulesets_created_by_created_at", table_name="rulesets")
    op.drop_table("rulesets")
    op.execute("DROP INDEX IF EXISTS ix_skills_search")
    op.drop_index("ix_skills_tags_gin", table_name="skills")
    op.drop_index("ix_skills_source", table_name="skills")
    op.drop_index("ix_skills_is_public_created_at", table_name="skills")
    op.drop_index("ix_skills_created_by_created_at", table_name="skills")
    op.drop_table("skills")
