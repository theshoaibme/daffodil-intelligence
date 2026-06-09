"""Baseline schema for existing application tables.

Revision ID: 001_baseline
Revises:
Create Date: 2026-06-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("student_id", sa.String(50)),
        sa.Column("department", sa.String(100)),
        sa.Column("semester", sa.Integer()),
        sa.Column("role", sa.String(20), server_default="student"),
        sa.Column("cgpa", sa.Float()),
        sa.Column("avatar_url", sa.String(512)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_student_id", "users", ["student_id"], unique=True)

    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(255)),
        sa.Column("agent_type", sa.String(50)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_chats_id", "chats", ["id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chat_id", sa.Integer(), sa.ForeignKey("chats.id")),
        sa.Column("role", sa.String(20)),
        sa.Column("content", sa.Text()),
        sa.Column("meta", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_id", "messages", ["id"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("session_type", sa.String(50)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime()),
    )
    op.create_index("ix_sessions_id", "sessions", ["id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255)),
        sa.Column("content", sa.Text()),
        sa.Column("doc_type", sa.String(50)),
        sa.Column("doc_metadata", sa.JSON()),
        sa.Column("embedding", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_documents_id", "documents", ["id"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_tickets_id", "tickets", ["id"])


def downgrade() -> None:
    op.drop_table("tickets")
    op.drop_table("documents")
    op.drop_table("sessions")
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("users")
