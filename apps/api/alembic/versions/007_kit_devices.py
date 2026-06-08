"""Kit device pairing and audit tables.

Revision ID: 007_kit_devices
Revises: 004_agent_memories
Create Date: 2026-06-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_kit_devices"
down_revision: Union[str, None] = "004_agent_memories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kit_devices",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False, server_default="desktop"),
        sa.Column("device_secret", sa.String(128), nullable=False),
        sa.Column("allowed_commands", postgresql.JSONB(), nullable=False, server_default='["screen","input","file_read","file_write","record"]'),
        sa.Column("allowed_roots", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("ws_url", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_kit_devices_user_id", "kit_devices", ["user_id"])

    op.create_table(
        "kit_pairing_codes",
        sa.Column("code", sa.String(8), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "kit_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("device_id", sa.String(64), sa.ForeignKey("kit_devices.id", ondelete="SET NULL")),
        sa.Column("command", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("success", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_kit_audit_events_user_id", "kit_audit_events", ["user_id"])
    op.create_index("ix_kit_audit_events_device_id", "kit_audit_events", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_kit_audit_events_device_id", table_name="kit_audit_events")
    op.drop_index("ix_kit_audit_events_user_id", table_name="kit_audit_events")
    op.drop_table("kit_audit_events")
    op.drop_table("kit_pairing_codes")
    op.drop_index("ix_kit_devices_user_id", table_name="kit_devices")
    op.drop_table("kit_devices")
