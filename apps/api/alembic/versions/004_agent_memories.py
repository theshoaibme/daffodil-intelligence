"""Agent memories table for unified deep memory.

Revision ID: 004_agent_memories
Revises: 003_hub_tables
Create Date: 2026-06-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_agent_memories"
down_revision: Union[str, None] = "003_hub_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_memories",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False, server_default="main"),
        sa.Column("scope", sa.String(32), nullable=False, server_default="root"),
        sa.Column("parent_agent_id", sa.String(64), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("memory_type", sa.String(64), nullable=False, server_default="fact"),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="private"),
        sa.Column("source", sa.String(32), nullable=False, server_default="system"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("qdrant_point_id", sa.String(64), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "content_hash", name="uq_agent_memories_user_hash"),
    )
    op.create_index("ix_agent_memories_user_id", "agent_memories", ["user_id"])
    op.create_index("ix_agent_memories_agent_id", "agent_memories", ["agent_id"])
    op.create_index("ix_agent_memories_memory_type", "agent_memories", ["memory_type"])
    op.create_index("ix_agent_memories_content_hash", "agent_memories", ["content_hash"])
    op.create_index(
        "ix_agent_memories_user_agent_type",
        "agent_memories",
        ["user_id", "agent_id", "memory_type"],
    )
    op.create_index(
        "ix_agent_memories_metadata_gin",
        "agent_memories",
        ["metadata"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_agent_memories_metadata_gin", table_name="agent_memories")
    op.drop_index("ix_agent_memories_user_agent_type", table_name="agent_memories")
    op.drop_index("ix_agent_memories_content_hash", table_name="agent_memories")
    op.drop_index("ix_agent_memories_memory_type", table_name="agent_memories")
    op.drop_index("ix_agent_memories_agent_id", table_name="agent_memories")
    op.drop_index("ix_agent_memories_user_id", table_name="agent_memories")
    op.drop_table("agent_memories")
