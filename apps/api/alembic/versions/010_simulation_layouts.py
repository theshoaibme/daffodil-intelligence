"""Simulation canvas layout storage per user.

Revision ID: 010_simulation_layouts
Revises: 009_ai_runtime_tables
Create Date: 2026-06-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "010_simulation_layouts"
down_revision: Union[str, None] = "009_ai_runtime_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _has_table("simulation_layouts"):
        op.create_table(
            "simulation_layouts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("custom_layout", sa.JSON(), nullable=True),
            sa.Column("default_layout", sa.JSON(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_simulation_layouts_user_id",
            "simulation_layouts",
            ["user_id"],
            unique=True,
        )


def downgrade() -> None:
    if _has_table("simulation_layouts"):
        op.drop_index("ix_simulation_layouts_user_id", table_name="simulation_layouts")
        op.drop_table("simulation_layouts")
