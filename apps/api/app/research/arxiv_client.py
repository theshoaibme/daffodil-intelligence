"""Fetch real research papers from the arXiv API."""

from __future__ import annotations

import asyncio
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import AsyncIterator
from urllib.parse import quote

import httpx

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
REQUEST_DELAY_SEC = 3.0
PAGE_SIZE = 500

# arXiv search queries mapped to library categories (~910 papers each → 10k+ total)
CATEGORY_ARXIV_QUERIES: dict[str, str] = {
    "Machine Learning": "cat:cs.LG OR cat:stat.ML",
    "Natural Language Processing": "cat:cs.CL",
    "Computer Vision": "cat:cs.CV",
    "Computer Science": "cat:cs.AI OR cat:cs.DS OR cat:cs.SE OR cat:cs.PL",
    "Data Science": "cat:stat.ME OR cat:stat.AP OR cat:cs.DB",
    "Cybersecurity": "cat:cs.CR",
    "Robotics": "cat:cs.RO",
    "Quantum Computing": "cat:quant-ph",
    "Bioinformatics": "cat:q-bio.BM OR cat:q-bio.GN OR cat:q-bio.QM",
    "AI & Education": '(all:"artificial intelligence" OR all:"machine learning") AND (all:education OR all:"learning analytics" OR all:pedagogy)',
    "Smart Grids": 'all:"smart grid" OR all:"power system" OR all:"renewable energy" OR cat:eess.SY',
}


@dataclass(frozen=True)
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: str
    year: str
    abstract: str
    category: str
    tags: list[str]
    url: str
    pdf_url: str
    pdf_file_name: str

    @property
    def paper_id(self) -> str:
        safe = re.sub(r"[^a-zA-Z0-9._-]", "-", self.arxiv_id)
        return f"arxiv-{safe}"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _arxiv_id_from_entry(entry: ET.Element) -> str | None:
    raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
    if not raw_id:
        return None
    match = re.search(r"arxiv\.org/abs/(.+)$", raw_id.strip())
    if not match:
        return None
    arxiv_id = match.group(1)
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
    return arxiv_id


def _parse_entry(entry: ET.Element, category: str) -> ArxivPaper | None:
    arxiv_id = _arxiv_id_from_entry(entry)
    if not arxiv_id:
        return None

    title = _clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
    if not title:
        return None

    author_nodes = entry.findall("atom:author", ATOM_NS)
    authors = ", ".join(
        _clean_text(node.findtext("atom:name", default="", namespaces=ATOM_NS))
        for node in author_nodes
        if node.findtext("atom:name", default="", namespaces=ATOM_NS)
    )
    if not authors:
        authors = "Unknown"

    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
    year = published[:4] if len(published) >= 4 else "2024"

    abstract = _clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
    if len(abstract) < 40:
        abstract = f"Research paper from arXiv ({arxiv_id}). {title}"

    tags = [
        node.attrib.get("term", "")
        for node in entry.findall("atom:category", ATOM_NS)
        if node.attrib.get("term")
    ][:6]

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title[:512],
        authors=authors[:512],
        year=year[:8],
        abstract=abstract[:8000],
        category=category,
        tags=tags or [category],
        url=f"https://arxiv.org/abs/{arxiv_id}",
        pdf_url=pdf_url,
        pdf_file_name=f"{arxiv_id.replace('/', '_')}.pdf",
    )


def _parse_feed(xml_text: str, category: str) -> list[ArxivPaper]:
    root = ET.fromstring(xml_text)
    papers: list[ArxivPaper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        paper = _parse_entry(entry, category)
        if paper:
            papers.append(paper)
    return papers


async def iter_category_papers(
    category: str,
    search_query: str,
    *,
    limit: int,
    seen_ids: set[str],
    client: httpx.AsyncClient,
) -> AsyncIterator[ArxivPaper]:
    """Yield up to `limit` unique papers for a category."""
    collected = 0
    start = 0

    while collected < limit:
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(PAGE_SIZE, limit - collected + 50),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API}?search_query={quote(params['search_query'])}&start={params['start']}&max_results={params['max_results']}&sortBy={params['sortBy']}&sortOrder={params['sortOrder']}"

        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        batch = _parse_feed(response.text, category)

        if not batch:
            break

        for paper in batch:
            if paper.arxiv_id in seen_ids:
                continue
            seen_ids.add(paper.arxiv_id)
            yield paper
            collected += 1
            if collected >= limit:
                return

        if len(batch) < params["max_results"]:
            break

        start += len(batch)
        await asyncio.sleep(REQUEST_DELAY_SEC)
