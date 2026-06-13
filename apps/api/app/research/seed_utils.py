"""Shared helpers for research paper seeding."""

from __future__ import annotations

import re


def derive_arxiv_pdf(url: str | None) -> tuple[str | None, str | None]:
    """Return (pdf_url, pdf_file_name) when `url` points to an arXiv abstract page."""
    if not url:
        return None, None
    match = re.search(r"arxiv\.org/abs/([^#?\s]+)", url, re.IGNORECASE)
    if not match:
        return None, None
    arxiv_id = re.sub(r"v\d+$", "", match.group(1))
    safe_name = arxiv_id.replace("/", "_")
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf", f"{safe_name}.pdf"
