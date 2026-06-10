"""Telegram sessions, pending registrations, and outbound queue in PostgreSQL.

Revision ID: 008_telegram_pg_stores
Revises: 007_kit_devices
Create Date: 2026-06-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "008_telegram_pg_stores"
down_revision: Union[str, None] = "007_kit_devices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    bind = op.get_bind()
    return name in {i["name"] for i in inspect(bind).get_indexes(table)}


def upgrade() -> None:
    if _has_column("users", "password_hash"):
        op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)

    user_columns = {
        "telegram_id": sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        "phone": sa.Column("phone", sa.String(32), nullable=True),
        "auth_provider": sa.Column("auth_provider", sa.String(16), server_default="email", nullable=False),
        "email_verified": sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        "first_name": sa.Column("first_name", sa.String(128), nullable=True),
        "last_name": sa.Column("last_name", sa.String(128), nullable=True),
        "telegram_username": sa.Column("telegram_username", sa.String(128), nullable=True),
        "last_login": sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    }
    for name, col in user_columns.items():
        if not _has_column("users", name):
            op.add_column("users", col)

    if _has_column("users", "telegram_id") and not _has_index("users", "ix_users_telegram_id"):
        op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    if not _has_table("telegram_profile_sessions"):
        op.create_table(
            "telegram_profile_sessions",
            sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
            sa.Column("username", sa.String(128), server_default="", nullable=False),
            sa.Column("first_name", sa.String(128), server_default="", nullable=False),
            sa.Column("last_name", sa.String(128), server_default="", nullable=False),
            sa.Column("full_name", sa.String(255), server_default="", nullable=False),
            sa.Column("role", sa.String(32), server_default="", nullable=False),
            sa.Column("phone", sa.String(32), server_default="", nullable=False),
            sa.Column("email", sa.String(255), server_default="", nullable=False),
            sa.Column("pending_password", sa.String(255), server_default="", nullable=False),
            sa.Column("student_id", sa.String(50), server_default="", nullable=False),
            sa.Column("department", sa.String(100), server_default="", nullable=False),
            sa.Column("step", sa.String(64), server_default="auth_menu", nullable=False),
            sa.Column("mode", sa.String(32), server_default="", nullable=False),
            sa.Column("selected_agent_id", sa.String(64), server_default="", nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    if not _has_table("pending_registrations"):
        op.create_table(
            "pending_registrations",
            sa.Column("email", sa.String(255), primary_key=True),
            sa.Column("accept_terms", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("first_name", sa.String(128), server_default="", nullable=False),
            sa.Column("last_name", sa.String(128), server_default="", nullable=False),
            sa.Column("password_hash", sa.String(255), server_default="", nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_pending_registrations_expires_at", "pending_registrations", ["expires_at"])

    if not _has_table("telegram_outbound_queue"):
        op.create_table(
            "telegram_outbound_queue",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("kind", sa.String(64), nullable=False),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("payload", postgresql.JSONB(), server_default="{}", nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_telegram_outbound_queue_created_at", "telegram_outbound_queue", ["created_at"])


def downgrade() -> None:
    if _has_table("telegram_outbound_queue"):
        op.drop_index("ix_telegram_outbound_queue_created_at", table_name="telegram_outbound_queue")
        op.drop_table("telegram_outbound_queue")
    if _has_table("pending_registrations"):
        op.drop_index("ix_pending_registrations_expires_at", table_name="pending_registrations")
        op.drop_table("pending_registrations")
    if _has_table("telegram_profile_sessions"):
        op.drop_table("telegram_profile_sessions")
    if _has_column("users", "telegram_id"):
        op.drop_index("ix_users_telegram_id", table_name="users")
    for col in (
        "last_login",
        "telegram_username",
        "last_name",
        "first_name",
        "email_verified",
        "auth_provider",
        "phone",
        "telegram_id",
    ):
        if _has_column("users", col):
            op.drop_column("users", col)
    if _has_column("users", "password_hash"):
        op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
