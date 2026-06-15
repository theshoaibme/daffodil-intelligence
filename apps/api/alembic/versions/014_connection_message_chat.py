"""Add direction and message type to connection correspondence.

Revision ID: 014_connection_message_chat
Revises: 013_research_connections
Create Date: 2026-06-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "014_connection_message_chat"
down_revision: Union[str, None] = "013_research_connections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column("connection_correspondence", "direction"):
        op.add_column(
            "connection_correspondence",
            sa.Column("direction", sa.String(length=16), nullable=False, server_default="outgoing"),
        )
    if not _has_column("connection_correspondence", "sender_name"):
        op.add_column(
            "connection_correspondence",
            sa.Column("sender_name", sa.String(length=255), nullable=True),
        )
    if not _has_column("connection_correspondence", "message_type"):
        op.add_column(
            "connection_correspondence",
            sa.Column("message_type", sa.String(length=16), nullable=False, server_default="formal"),
        )


def downgrade() -> None:
    if _has_column("connection_correspondence", "message_type"):
        op.drop_column("connection_correspondence", "message_type")
    if _has_column("connection_correspondence", "sender_name"):
        op.drop_column("connection_correspondence", "sender_name")
    if _has_column("connection_correspondence", "direction"):
        op.drop_column("connection_correspondence", "direction")
