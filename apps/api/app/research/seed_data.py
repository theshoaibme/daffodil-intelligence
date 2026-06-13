"""Load research categories and seed papers from bundled JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SEED_PATH = Path(__file__).with_name("papers_seed.json")

with _SEED_PATH.open(encoding="utf-8") as f:
    _DATA: dict[str, Any] = json.load(f)

RESEARCH_CATEGORIES: list[str] = list(_DATA.get("categories", []))
SEED_PAPERS: list[dict[str, Any]] = list(_DATA.get("papers", []))
CATEGORY_OTHERS = "Others"
