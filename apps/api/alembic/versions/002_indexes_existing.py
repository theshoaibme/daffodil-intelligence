"""Add FK and composite indexes on existing tables.

Revision ID: 002_indexes_existing
Revises: 001_baseline
Create Date: 2026-06-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002_indexes_existing"
down_revision: Union[str, None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_chats_user_id_created_at",
        "chats",
        ["user_id", "created_at"],
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index("ix_messages_chat_id_created_at", "messages", ["chat_id", "created_at"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_tickets_user_id", "tickets", ["user_id"])
    op.create_index(
        "ix_tickets_status_created_at",
        "tickets",
        ["status", "created_at"],
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade() -> None:
    op.drop_index("ix_tickets_status_created_at", table_name="tickets")
    op.drop_index("ix_tickets_user_id", table_name="tickets")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_messages_chat_id_created_at", table_name="messages")
    op.drop_index("ix_chats_user_id_created_at", table_name="chats")
