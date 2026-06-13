"""Research paper library — public browse and authenticated CRUD."""

from __future__ import annotations

import re
import time
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.research import ResearchPaper
from ..research.seed_data import CATEGORY_OTHERS, RESEARCH_CATEGORIES, SEED_PAPERS

router = APIRouter(prefix="/research", tags=["research"])


class ResearchPaperResponse(BaseModel):
    id: str
    title: str
    authors: str
    year: str
    citations: int
    source: str
    category: str
    abstract: str
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_file_name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_public: bool = True


class ResearchPaperListResponse(BaseModel):
    items: List[ResearchPaperResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class ResearchCategoriesResponse(BaseModel):
    categories: List[str]
    form_categories: List[str]


class ResearchPaperCreate(BaseModel):
    title: str
    authors: str
    year: str
    source: str = "Local Library"
    category: str
    abstract: str
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_file_name: Optional[str] = None
    tags: Optional[List[str]] = None
    citations: int = 0
    is_public: bool = True


class ResearchPaperUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_file_name: Optional[str] = None
    tags: Optional[List[str]] = None
    citations: Optional[int] = None
    is_public: Optional[bool] = None


def _to_response(row: ResearchPaper) -> ResearchPaperResponse:
    tags = row.tags if isinstance(row.tags, list) else []
    return ResearchPaperResponse(
        id=row.id,
        title=row.title,
        authors=row.authors,
        year=row.year,
        citations=row.citations or 0,
        source=row.source,
        category=row.category,
        abstract=row.abstract,
        url=row.url,
        pdf_url=row.pdf_url,
        pdf_file_name=row.pdf_file_name,
        tags=[str(t) for t in tags],
        is_public=bool(row.is_public),
    )


def generate_paper_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9\s]", "", title.lower()).strip()
    slug = re.sub(r"\s+", "-", slug)[:40]
    suffix = format(int(time.time() * 1000), "x")
    return f"{slug}-{suffix}" if slug else f"paper-{suffix}"


async def _merged_categories(db: AsyncSession) -> list[str]:
    result = await db.execute(select(ResearchPaper.category).distinct())
    db_cats = {row[0] for row in result.all() if row[0]}
    return sorted(set(RESEARCH_CATEGORIES) | db_cats)


def _apply_search(stmt, q: Optional[str]):
    if not q or not q.strip():
        return stmt
    term = f"%{q.strip().lower()}%"
    return stmt.where(
        or_(
            func.lower(ResearchPaper.title).like(term),
            func.lower(ResearchPaper.authors).like(term),
            func.lower(ResearchPaper.abstract).like(term),
            func.lower(ResearchPaper.category).like(term),
        )
    )


@router.get("/categories", response_model=ResearchCategoriesResponse)
async def list_categories(db: AsyncSession = Depends(get_db)):
    categories = await _merged_categories(db)
    form = list(categories)
    if CATEGORY_OTHERS not in form:
        form.append(CATEGORY_OTHERS)
    return ResearchCategoriesResponse(categories=categories, form_categories=form)


@router.get("/papers", response_model=ResearchPaperListResponse)
async def list_public_papers(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(16, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ResearchPaper).where(ResearchPaper.is_public.is_(True))
    if category and category not in ("All", ""):
        stmt = stmt.where(ResearchPaper.category == category)
    stmt = _apply_search(stmt, q)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(ResearchPaper.created_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    total_pages = max(1, (total + limit - 1) // limit)
    return ResearchPaperListResponse(
        items=[_to_response(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/papers/{paper_id}", response_model=ResearchPaperResponse)
async def get_public_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(ResearchPaper, paper_id)
    if not row or not row.is_public:
        raise HTTPException(status_code=404, detail="Paper not found")
    return _to_response(row)


@router.get("/manage/papers", response_model=ResearchPaperListResponse)
async def list_manage_papers(
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    _ = user
    stmt = select(ResearchPaper)
    stmt = _apply_search(stmt, q)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(ResearchPaper.created_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    total_pages = max(1, (total + limit - 1) // limit)
    return ResearchPaperListResponse(
        items=[_to_response(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("/papers", response_model=ResearchPaperResponse, status_code=status.HTTP_201_CREATED)
async def create_paper(
    body: ResearchPaperCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = int(user["sub"])
    paper_id = generate_paper_id(body.title)

    row = ResearchPaper(
        id=paper_id,
        user_id=user_id,
        title=body.title.strip(),
        authors=body.authors.strip(),
        year=str(body.year).strip(),
        citations=body.citations,
        source=(body.source or "Local Library").strip(),
        category=body.category.strip(),
        abstract=body.abstract.strip(),
        url=body.url.strip() if body.url else None,
        pdf_url=body.pdf_url.strip() if body.pdf_url else None,
        pdf_file_name=body.pdf_file_name.strip() if body.pdf_file_name else None,
        tags=body.tags or [],
        is_public=body.is_public,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_response(row)


@router.put("/papers/{paper_id}", response_model=ResearchPaperResponse)
async def update_paper(
    paper_id: str,
    body: ResearchPaperUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    _ = user
    row = await db.get(ResearchPaper, paper_id)
    if not row:
        raise HTTPException(status_code=404, detail="Paper not found")

    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "tags" and value is None:
            value = []
        if key in ("url", "pdf_url", "pdf_file_name") and isinstance(value, str):
            value = value.strip() or None
        setattr(row, key, value)

    await db.commit()
    await db.refresh(row)
    return _to_response(row)


@router.delete("/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    _ = user
    row = await db.get(ResearchPaper, paper_id)
    if not row:
        raise HTTPException(status_code=404, detail="Paper not found")
    await db.delete(row)
    await db.commit()


def seed_paper_rows() -> list[dict[str, Any]]:
    """Rows for Alembic bulk insert."""
    rows: list[dict[str, Any]] = []
    for paper in SEED_PAPERS:
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
