#!/usr/bin/env python3
"""CLI entry: seed 10k+ real arXiv papers with PDFs."""

import sys
from pathlib import Path

# Allow `python scripts/seed_research_papers.py` from apps/api
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.research.bulk_seed import main

if __name__ == "__main__":
    main()
