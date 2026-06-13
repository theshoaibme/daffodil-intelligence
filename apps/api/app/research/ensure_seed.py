"""Ensure bundled research papers exist when the library table is empty."""

from __future__ import annotations

import logging

from sqlalchemy import select

from ..core.database import get_session_maker, is_mock_database
from ..models.research import ResearchPaper
from .seed_data import SEED_PAPERS
from .seed_utils import derive_arxiv_pdf

logger = logging.getLogger("app.research")


async def ensure_research_papers_seeded() -> int:
    """Insert bundled seed papers that are not yet in the database. Returns rows inserted."""
    if is_mock_database() or get_session_maker() is None:
        return 0

    session_maker = get_session_maker()
    if session_maker is None:
        return 0

    async with session_maker() as session:
        existing_ids = set((await session.execute(select(ResearchPaper.id))).scalars().all())

        inserted = 0
        for paper in SEED_PAPERS:
            if paper["id"] in existing_ids:
                continue

            pdf_url = paper.get("pdfUrl") or paper.get("pdf_url")
            pdf_file_name = paper.get("pdfFileName") or paper.get("pdf_file_name")
            if not pdf_url:
                pdf_url, pdf_file_name = derive_arxiv_pdf(paper.get("url"))

            session.add(
                ResearchPaper(
                    id=paper["id"],
                    user_id=None,
                    title=paper["title"],
                    authors=paper["authors"],
                    year=str(paper["year"]),
                    citations=int(paper.get("citations") or 0),
                    source=paper.get("source") or "Local Library",
                    category=paper["category"],
                    abstract=paper["abstract"],
                    url=paper.get("url"),
                    pdf_url=pdf_url,
                    pdf_file_name=pdf_file_name,
                    tags=paper.get("tags") or [],
                    is_public=True,
                )
            )
            inserted += 1

        if inserted:
            await session.commit()
            logger.info("Seeded %s research papers", inserted)
        return inserted
