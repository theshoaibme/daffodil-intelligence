"""Backfill research paper seed data when migration 011 created an empty table.

Revision ID: 012_research_papers_seed
Revises: 011_research_papers
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

revision: str = "012_research_papers_seed"
down_revision: Union[str, None] = "011_research_papers"
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
        return

    bind = op.get_bind()
    count = bind.execute(sa.text("SELECT COUNT(*) FROM research_papers")).scalar_one()
    if count:
        return

    seed_rows = _load_seed_rows()
    if not seed_rows:
        return

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
    pass
