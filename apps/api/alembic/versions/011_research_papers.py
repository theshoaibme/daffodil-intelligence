"""Research papers library table and seed data.

Revision ID: 011_research_papers
Revises: 010_simulation_layouts
Create Date: 2026-06-13
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "011_research_papers"
down_revision: Union[str, None] = "010_simulation_layouts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def _load_seed_rows() -> list[dict]:
    seed_path = Path(__file__).resolve().parents[2] / "app" / "research" / "papers_seed.json"
    with seed_path.open(encoding="utf-8") as f:
        data = json.load(f)
    rows: list[dict] = []
    for paper in data.get("papers", []):
        rows.append(
            {
                "id": paper["id"],
                "user_id": None,
                "title": paper["title"],
                "authors": paper["authors"],
                "year": str(paper["year"]),
                "citations": int(paper.get("citations") or 0),
                "source": paper.get("source") or "Local Library",
                "category": paper["category"],
                "abstract": paper["abstract"],
                "url": paper.get("url"),
                "pdf_url": paper.get("pdfUrl") or paper.get("pdf_url"),
                "pdf_file_name": paper.get("pdfFileName") or paper.get("pdf_file_name"),
                "tags": paper.get("tags") or [],
                "is_public": True,
            }
        )
    return rows


def upgrade() -> None:
    if not _has_table("research_papers"):
        op.create_table(
            "research_papers",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(length=512), nullable=False),
            sa.Column("authors", sa.String(length=512), nullable=False),
            sa.Column("year", sa.String(length=8), nullable=False),
            sa.Column("citations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("source", sa.String(length=255), nullable=False, server_default="Local Library"),
            sa.Column("category", sa.String(length=128), nullable=False),
            sa.Column("abstract", sa.Text(), nullable=False),
            sa.Column("url", sa.String(length=2048), nullable=True),
            sa.Column("pdf_url", sa.Text(), nullable=True),
            sa.Column("pdf_file_name", sa.String(length=512), nullable=True),
            sa.Column("tags", JSONB(), nullable=False, server_default="[]"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_research_papers_category", "research_papers", ["category"])
        op.create_index("ix_research_papers_is_public_created_at", "research_papers", ["is_public", "created_at"])
        op.create_index("ix_research_papers_user_id", "research_papers", ["user_id"])

        seed_rows = _load_seed_rows()
        if seed_rows:
            op.bulk_insert(
                sa.table(
                    "research_papers",
                    sa.column("id", sa.String),
                    sa.column("user_id", sa.Integer),
                    sa.column("title", sa.String),
                    sa.column("authors", sa.String),
                    sa.column("year", sa.String),
                    sa.column("citations", sa.Integer),
                    sa.column("source", sa.String),
                    sa.column("category", sa.String),
                    sa.column("abstract", sa.Text),
                    sa.column("url", sa.String),
                    sa.column("pdf_url", sa.Text),
                    sa.column("pdf_file_name", sa.String),
                    sa.column("tags", JSONB),
                    sa.column("is_public", sa.Boolean),
                ),
                seed_rows,
            )


def downgrade() -> None:
    if _has_table("research_papers"):
        op.drop_index("ix_research_papers_user_id", table_name="research_papers")
        op.drop_index("ix_research_papers_is_public_created_at", table_name="research_papers")
        op.drop_index("ix_research_papers_category", table_name="research_papers")
        op.drop_table("research_papers")
