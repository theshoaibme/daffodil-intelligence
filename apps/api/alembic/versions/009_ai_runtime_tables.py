"""AI runtime tables: event_log, workflows, workflow_nodes.

Revision ID: 009_ai_runtime_tables
Revises: 008_telegram_pg_stores
Create Date: 2026-06-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "009_ai_runtime_tables"
down_revision: Union[str, None] = "008_telegram_pg_stores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _has_table("event_log"):
        op.create_table(
            "event_log",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("session_id", sa.String(128), nullable=False, index=True),
            sa.Column("turn_id", sa.String(128), nullable=False, index=True),
            sa.Column("seq", sa.BigInteger(), nullable=False),
            sa.Column("envelope", postgresql.JSONB(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "idx_event_log_session_seq",
            "event_log",
            ["session_id", "seq"],
        )

    if not _has_table("workflows"):
        op.create_table(
            "workflows",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("chat_id", sa.Integer(), sa.ForeignKey("chats.id"), nullable=True, index=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("definition", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("checkpoint", postgresql.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not _has_table("workflow_nodes"):
        op.create_table(
            "workflow_nodes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "workflow_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("workflows.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("agent_id", sa.String(128), nullable=True),
            sa.Column("kind", sa.String(32), nullable=False, server_default="agent"),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("input", postgresql.JSONB(), nullable=True),
            sa.Column("output", postgresql.JSONB(), nullable=True),
            sa.Column("parallel_group", sa.String(64), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    if _has_table("workflow_nodes"):
        op.drop_table("workflow_nodes")
    if _has_table("workflows"):
        op.drop_table("workflows")
    if _has_table("event_log"):
        op.drop_index("idx_event_log_session_seq", table_name="event_log")
        op.drop_table("event_log")
