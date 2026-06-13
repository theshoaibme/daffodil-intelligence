"""Research connections API — network, requests, and formal correspondence."""

from __future__ import annotations

import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..connections.build_network import NetworkNode, build_network_from_papers
from ..core.database import get_db
from ..core.security import decode_token, get_current_user, security
from ..models.connection import ConnectionCorrespondence, UserResearchConnection
from ..models.research import ResearchPaper

router = APIRouter(prefix="/connections", tags=["connections"])

ConnectionStatus = Literal["available", "pending", "connected"]
ConnectionKind = Literal["researcher", "institution"]


class FeaturedPaperResponse(BaseModel):
    id: str
    title: str


class NetworkConnectionResponse(BaseModel):
    id: str
    kind: ConnectionKind
    name: str
    subtitle: str
    focus: str
    paper_count: int
    citations: int
    paper_ids: List[str]
    featured_paper: Optional[FeaturedPaperResponse] = None
    status: ConnectionStatus = "available"


class NetworkStatsResponse(BaseModel):
    researchers: int
    institutions: int
    connected: int


class NetworkListResponse(BaseModel):
    items: List[NetworkConnectionResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    stats: NetworkStatsResponse


class CorrespondenceCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=512)
    salutation: str = Field(default="", max_length=255)
    body: str = Field(..., min_length=1)
    closing: str = Field(default="", max_length=2000)
    purpose: Optional[str] = Field(default=None, max_length=64)


class CorrespondenceResponse(BaseModel):
    id: str
    connection_id: str
    subject: str
    salutation: str
    body: str
    closing: str
    purpose: Optional[str] = None
    sent_at: str
    direction: Literal["outgoing"] = "outgoing"


class ConnectionActionResponse(BaseModel):
    target_id: str
    status: ConnectionStatus


async def _optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None


def _user_id(user: dict) -> int:
    return int(user["sub"])


async def _load_public_papers(db: AsyncSession, limit: int = 100) -> list[ResearchPaper]:
    stmt = (
        select(ResearchPaper)
        .where(ResearchPaper.is_public.is_(True))
        .order_by(ResearchPaper.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def _load_user_statuses(db: AsyncSession, user_id: int) -> dict[str, str]:
    rows = (
        await db.execute(
            select(UserResearchConnection.target_id, UserResearchConnection.status).where(
                UserResearchConnection.user_id == user_id
            )
        )
    ).all()
    return {target_id: row_status for target_id, row_status in rows}


def _node_to_response(node: NetworkNode, node_status: str) -> NetworkConnectionResponse:
    featured = None
    if node.featured_paper:
        featured = FeaturedPaperResponse(id=node.featured_paper.id, title=node.featured_paper.title)
    return NetworkConnectionResponse(
        id=node.id,
        kind=node.kind,
        name=node.name,
        subtitle=node.subtitle,
        focus=node.focus,
        paper_count=node.paper_count,
        citations=node.citations,
        paper_ids=node.paper_ids,
        featured_paper=featured,
        status=node_status,  # type: ignore[arg-type]
    )


def _filter_nodes(
    nodes: list[NetworkNode],
    *,
    q: Optional[str],
    kind: Optional[str],
    status_filter: Optional[str],
    statuses: dict[str, str],
) -> list[NetworkNode]:
    q_lower = (q or "").strip().lower()
    filtered: list[NetworkNode] = []

    for node in nodes:
        node_status = statuses.get(node.id, "available")
        if kind and kind not in ("all", "") and node.kind != kind:
            continue
        if status_filter == "connected" and node_status != "connected":
            continue
        if q_lower:
            haystack = " ".join(
                [
                    node.name.lower(),
                    node.subtitle.lower(),
                    node.focus.lower(),
                    node.featured_paper.title.lower() if node.featured_paper else "",
                ]
            )
            if q_lower not in haystack:
                continue
        filtered.append(node)

    return filtered


async def _get_target_node(db: AsyncSession, target_id: str) -> NetworkNode:
    papers = await _load_public_papers(db)
    nodes = build_network_from_papers(papers)
    for node in nodes:
        if node.id == target_id:
            return node
    raise HTTPException(status_code=404, detail="Connection target not found")


@router.get("/network", response_model=NetworkListResponse)
async def list_network(
    q: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by connected status"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(_optional_user),
):
    papers = await _load_public_papers(db)
    nodes = build_network_from_papers(papers)

    statuses: dict[str, str] = {}
    if user:
        statuses = await _load_user_statuses(db, _user_id(user))

    filtered = _filter_nodes(nodes, q=q, kind=kind, status_filter=status, statuses=statuses)
    total = len(filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    page_nodes = filtered[start : start + limit]

    researchers = sum(1 for n in nodes if n.kind == "researcher")
    institutions = sum(1 for n in nodes if n.kind == "institution")
    connected = sum(1 for s in statuses.values() if s == "connected")

    items = [_node_to_response(n, statuses.get(n.id, "available")) for n in page_nodes]

    return NetworkListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        stats=NetworkStatsResponse(
            researchers=researchers,
            institutions=institutions,
            connected=connected,
        ),
    )


@router.post("/{target_id}/request", response_model=ConnectionActionResponse)
async def request_connection(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = _user_id(user)
    node = await _get_target_node(db, target_id)

    existing = (
        await db.execute(
            select(UserResearchConnection).where(
                UserResearchConnection.user_id == user_id,
                UserResearchConnection.target_id == target_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        if existing.status == "connected":
            return ConnectionActionResponse(target_id=target_id, status="connected")
        existing.status = "pending"
        await db.commit()
        return ConnectionActionResponse(target_id=target_id, status="pending")

    db.add(
        UserResearchConnection(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_id=target_id,
            target_kind=node.kind,
            status="pending",
        )
    )
    await db.commit()
    return ConnectionActionResponse(target_id=target_id, status="pending")


@router.post("/{target_id}/accept", response_model=ConnectionActionResponse)
async def accept_connection(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = _user_id(user)
    node = await _get_target_node(db, target_id)

    row = (
        await db.execute(
            select(UserResearchConnection).where(
                UserResearchConnection.user_id == user_id,
                UserResearchConnection.target_id == target_id,
            )
        )
    ).scalar_one_or_none()

    if row is None:
        db.add(
            UserResearchConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                target_id=target_id,
                target_kind=node.kind,
                status="connected",
            )
        )
    else:
        row.status = "connected"

    await db.commit()
    return ConnectionActionResponse(target_id=target_id, status="connected")


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connection(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = _user_id(user)
    row = (
        await db.execute(
            select(UserResearchConnection).where(
                UserResearchConnection.user_id == user_id,
                UserResearchConnection.target_id == target_id,
            )
        )
    ).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


@router.get("/{target_id}/messages", response_model=List[CorrespondenceResponse])
async def list_messages(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = _user_id(user)
    await _get_target_node(db, target_id)

    rows = (
        await db.execute(
            select(ConnectionCorrespondence)
            .where(
                ConnectionCorrespondence.user_id == user_id,
                ConnectionCorrespondence.target_id == target_id,
            )
            .order_by(ConnectionCorrespondence.created_at.asc())
        )
    ).scalars().all()

    return [
        CorrespondenceResponse(
            id=row.id,
            connection_id=row.target_id,
            subject=row.subject,
            salutation=row.salutation,
            body=row.body,
            closing=row.closing,
            purpose=row.purpose,
            sent_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


@router.post("/{target_id}/messages", response_model=CorrespondenceResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    target_id: str,
    body: CorrespondenceCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = _user_id(user)
    node = await _get_target_node(db, target_id)

    row = ConnectionCorrespondence(
        id=str(uuid.uuid4()),
        user_id=user_id,
        target_id=target_id,
        subject=body.subject.strip(),
        salutation=body.salutation.strip(),
        body=body.body.strip(),
        closing=body.closing.strip(),
        purpose=body.purpose,
    )
    db.add(row)

    conn = (
        await db.execute(
            select(UserResearchConnection).where(
                UserResearchConnection.user_id == user_id,
                UserResearchConnection.target_id == target_id,
            )
        )
    ).scalar_one_or_none()

    if conn is None:
        db.add(
            UserResearchConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                target_id=target_id,
                target_kind=node.kind,
                status="pending",
            )
        )
    elif conn.status != "connected":
        conn.status = "pending"

    await db.commit()
    await db.refresh(row)

    return CorrespondenceResponse(
        id=row.id,
        connection_id=row.target_id,
        subject=row.subject,
        salutation=row.salutation,
        body=row.body,
        closing=row.closing,
        purpose=row.purpose,
        sent_at=row.created_at.isoformat(),
    )


@router.get("/me/summary", response_model=NetworkStatsResponse)
async def connection_summary(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = _user_id(user)
    papers = await _load_public_papers(db)
    nodes = build_network_from_papers(papers)
    researchers = sum(1 for n in nodes if n.kind == "researcher")
    institutions = sum(1 for n in nodes if n.kind == "institution")

    connected = (
        await db.execute(
            select(func.count())
            .select_from(UserResearchConnection)
            .where(
                UserResearchConnection.user_id == user_id,
                UserResearchConnection.status == "connected",
            )
        )
    ).scalar_one()

    return NetworkStatsResponse(
        researchers=researchers,
        institutions=institutions,
        connected=int(connected or 0),
    )
