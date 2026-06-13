"""Bulk-seed research papers from arXiv into PostgreSQL."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

import httpx
from sqlalchemy.dialects.postgresql import insert

from ..core.database import get_session_maker, init_db, is_mock_database
from ..models.research import ResearchPaper
from .arxiv_client import CATEGORY_ARXIV_QUERIES, iter_category_papers
from .seed_data import RESEARCH_CATEGORIES

logger = logging.getLogger("app.research.bulk_seed")

DEFAULT_MIN_TOTAL = 10_000


def _paper_to_row(paper) -> dict:
    return {
        "id": paper.paper_id,
        "user_id": None,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "citations": 0,
        "source": "arXiv",
        "category": paper.category,
        "abstract": paper.abstract,
        "url": paper.url,
        "pdf_url": paper.pdf_url,
        "pdf_file_name": paper.pdf_file_name,
        "tags": paper.tags,
        "is_public": True,
    }


async def seed_research_from_arxiv(
    *,
    min_total: int = DEFAULT_MIN_TOTAL,
    batch_size: int = 250,
    progress: Callable[[str], None] | None = None,
) -> dict[str, int]:
    """
    Fetch real arXiv papers (with PDF URLs) until at least `min_total` are stored.
    Returns stats: inserted, skipped, total_in_db.
    """
    if is_mock_database() or get_session_maker() is None:
        raise RuntimeError("Database is not available (mock mode).")

    session_maker = get_session_maker()
    if session_maker is None:
        raise RuntimeError("Database session maker is not initialized.")

    async with session_maker() as session:
        from sqlalchemy import func, select

        current_total = (await session.execute(select(func.count()).select_from(ResearchPaper))).scalar_one()

    if current_total >= min_total:
        log_msg = f"Already have {current_total} papers (>= {min_total}). Nothing to do."
        logger.info(log_msg)
        if progress:
            progress(log_msg)
        return {"inserted": 0, "skipped": 0, "total_in_db": current_total}

    remaining = min_total - current_total
    categories = list(RESEARCH_CATEGORIES) or list(CATEGORY_ARXIV_QUERIES.keys())
    per_category = max(1, (remaining + len(categories) - 1) // len(categories))

    seen_ids: set[str] = set()
    inserted = 0
    skipped = 0

    def log(msg: str) -> None:
        logger.info(msg)
        if progress:
            progress(msg)

    log(f"Seeding {remaining} more papers (~{per_category} per category)...")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for category in categories:
            query = CATEGORY_ARXIV_QUERIES.get(category)
            if not query:
                log(f"Skipping {category}: no arXiv query configured")
                continue

            log(f"Fetching {category} (target {per_category} papers)...")
            batch_rows: list[dict] = []
            category_count = 0

            async for paper in iter_category_papers(
                category,
                query,
                limit=per_category,
                seen_ids=seen_ids,
                client=client,
            ):
                batch_rows.append(_paper_to_row(paper))
                category_count += 1

                if len(batch_rows) >= batch_size:
                    n = await _insert_batch(session_maker, batch_rows)
                    inserted += n
                    skipped += len(batch_rows) - n
                    batch_rows.clear()
                    log(f"  {category}: {category_count} fetched, {inserted} inserted total")

            if batch_rows:
                n = await _insert_batch(session_maker, batch_rows)
                inserted += n
                skipped += len(batch_rows) - n

            log(f"  Done {category}: {category_count} papers")

    async with session_maker() as session:
        from sqlalchemy import func, select

        total_in_db = (await session.execute(select(func.count()).select_from(ResearchPaper))).scalar_one()

    return {"inserted": inserted, "skipped": skipped, "total_in_db": total_in_db}


async def _insert_batch(session_maker, rows: list[dict]) -> int:
    if not rows:
        return 0

    stmt = insert(ResearchPaper).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
    async with session_maker() as session:
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount or 0


async def run_bulk_seed_cli(min_total: int = DEFAULT_MIN_TOTAL) -> None:
    await init_db()
    stats = await seed_research_from_arxiv(
        min_total=min_total,
        progress=lambda msg: print(msg, flush=True),
    )
    print(
        f"\nBulk seed complete: inserted={stats['inserted']}, "
        f"skipped={stats['skipped']}, total_in_db={stats['total_in_db']}",
        flush=True,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed research papers from arXiv with PDF URLs")
    parser.add_argument(
        "--min-total",
        type=int,
        default=DEFAULT_MIN_TOTAL,
        help="Minimum total papers to seed (default: 10000)",
    )
    args = parser.parse_args()
    asyncio.run(run_bulk_seed_cli(min_total=args.min_total))


if __name__ == "__main__":
    main()
