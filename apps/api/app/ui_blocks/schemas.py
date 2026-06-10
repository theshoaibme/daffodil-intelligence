"""Pydantic models for structured UI blocks streamed to the web client."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

ALLOWED_BLOCK_SCHEMAS = frozenset(
    {
        "data_table",
        "key_value",
        "tabs",
        "status_card",
        "error_alert",
    }
)


class UiBlock(BaseModel):
    """Wire JSON uses ``schema``; Python field is ``block_type`` to avoid shadowing BaseModel.schema."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: f"ui-{uuid.uuid4().hex[:10]}")
    block_type: str = Field(alias="schema")
    title: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None


class TurnPresentation(BaseModel):
    summary: str = ""
    blocks: List[UiBlock] = Field(default_factory=list)


def ui_block_to_dict(block: UiBlock) -> Dict[str, Any]:
    return block.model_dump(by_alias=True)


def validate_block_payload(raw: Dict[str, Any]) -> UiBlock:
    schema = str(raw.get("schema") or "").strip()
    if schema not in ALLOWED_BLOCK_SCHEMAS:
        raise ValueError(f"Unsupported UI block schema: {schema}")
    data = raw.get("data")
    if not isinstance(data, dict):
        raise ValueError("UI block data must be an object")
    return UiBlock.model_validate(
        {
            "id": str(raw.get("id") or f"ui-{uuid.uuid4().hex[:10]}"),
            "schema": schema,
            "title": raw.get("title"),
            "data": data,
            "source": raw.get("source"),
        }
    )
