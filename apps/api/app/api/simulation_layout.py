"""Agent simulation canvas layout — synced with web localStorage."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.simulation import SimulationLayout

router = APIRouter(prefix="/simulation-layout", tags=["agents"])

SavedPositions = Dict[str, Dict[str, float]]


class SimulationLayoutUpdate(BaseModel):
    custom: Optional[SavedPositions] = None
    default: Optional[SavedPositions] = None


class SimulationLayoutResponse(BaseModel):
    custom: SavedPositions = Field(default_factory=dict)
    default: SavedPositions = Field(default_factory=dict)
    updated_at: Optional[str] = None


def _normalize_positions(raw: Any) -> SavedPositions:
    if not isinstance(raw, dict):
        return {}
    out: SavedPositions = {}
    for node_id, pos in raw.items():
        if not isinstance(pos, dict):
            continue
        try:
            x = float(pos.get("x"))
            y = float(pos.get("y"))
        except (TypeError, ValueError):
            continue
        out[str(node_id)] = {"x": x, "y": y}
    return out


async def _get_or_create(db: AsyncSession, user_id: int) -> SimulationLayout:
    result = await db.execute(
        select(SimulationLayout).where(SimulationLayout.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row:
        return row
    row = SimulationLayout(user_id=user_id, custom_layout={}, default_layout={})
    db.add(row)
    await db.flush()
    return row


@router.get("", response_model=SimulationLayoutResponse)
async def get_simulation_layout(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = int(user["sub"])
    result = await db.execute(
        select(SimulationLayout).where(SimulationLayout.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return SimulationLayoutResponse()
    return SimulationLayoutResponse(
        custom=_normalize_positions(row.custom_layout),
        default=_normalize_positions(row.default_layout),
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


@router.put("", response_model=SimulationLayoutResponse)
async def save_simulation_layout(
    body: SimulationLayoutUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = int(user["sub"])
    row = await _get_or_create(db, user_id)

    if body.custom is not None:
        row.custom_layout = _normalize_positions(body.custom)
    if body.default is not None:
        row.default_layout = _normalize_positions(body.default)

    await db.commit()
    await db.refresh(row)

    return SimulationLayoutResponse(
        custom=_normalize_positions(row.custom_layout),
        default=_normalize_positions(row.default_layout),
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )
