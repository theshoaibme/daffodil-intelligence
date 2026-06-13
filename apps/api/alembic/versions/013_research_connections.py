"""User research connections and formal correspondence tables.

Revision ID: 013_research_connections
Revises: 012_research_papers_seed
Create Date: 2026-06-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "013_research_connections"
down_revision: Union[str, None] = "012_research_papers_seed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _has_table("user_research_connections"):
        op.create_table(
            "user_research_connections",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("target_id", sa.String(length=128), nullable=False),
            sa.Column("target_kind", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("user_id", "target_id", name="uq_user_research_connection_target"),
        )
        op.create_index("ix_user_research_connections_user_id", "user_research_connections", ["user_id"])
        op.create_index("ix_user_research_connections_target_id", "user_research_connections", ["target_id"])

    if not _has_table("connection_correspondence"):
        op.create_table(
            "connection_correspondence",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("target_id", sa.String(length=128), nullable=False),
            sa.Column("subject", sa.String(length=512), nullable=False),
            sa.Column("salutation", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("closing", sa.Text(), nullable=False, server_default=""),
            sa.Column("purpose", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index(
            "ix_connection_correspondence_user_target",
            "connection_correspondence",
            ["user_id", "target_id"],
        )


def downgrade() -> None:
    if _has_table("connection_correspondence"):
        op.drop_index("ix_connection_correspondence_user_target", table_name="connection_correspondence")
        op.drop_table("connection_correspondence")
    if _has_table("user_research_connections"):
        op.drop_index("ix_user_research_connections_target_id", table_name="user_research_connections")
        op.drop_index("ix_user_research_connections_user_id", table_name="user_research_connections")
        op.drop_table("user_research_connections")
