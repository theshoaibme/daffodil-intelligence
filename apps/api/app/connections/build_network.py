"""Build research connection network from public papers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

ConnectionKind = Literal["researcher", "institution"]


@dataclass
class FeaturedPaper:
    id: str
    title: str


@dataclass
class NetworkNode:
    id: str
    kind: ConnectionKind
    name: str
    subtitle: str
    focus: str
    paper_count: int
    citations: int
    paper_ids: list[str]
    featured_paper: FeaturedPaper | None = None


@dataclass
class _ResearcherAgg:
    name: str
    sources: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    paper_ids: list[str] = field(default_factory=list)
    citations: int = 0
    top_citation: int = 0
    featured_paper: FeaturedPaper | None = None


@dataclass
class _InstitutionAgg:
    name: str
    categories: set[str] = field(default_factory=set)
    paper_ids: list[str] = field(default_factory=list)
    citations: int = 0
    top_citation: int = 0
    featured_paper: FeaturedPaper | None = None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def _parse_author_names(authors: str) -> list[str]:
    cleaned = re.sub(r"\([^)]*\)", "", authors)
    cleaned = re.sub(r"\bet al\.?\b", "", cleaned, flags=re.IGNORECASE).strip()
    parts = re.split(r",|&|\band\b", cleaned, flags=re.IGNORECASE)
    names: list[str] = []
    for part in parts:
        text = part.strip()
        if len(text) <= 1 or re.match(r"^(jr|sr|phd|md)$", text, re.IGNORECASE):
            continue
        names.append(text)
        if len(names) >= 4:
            break
    return names


def _format_author_name(raw: str) -> str:
    trimmed = raw.strip()
    if "." in trimmed and "," in trimmed:
        last, _, rest = trimmed.partition(",")
        last = last.strip()
        initials = rest.replace(".", " ").strip()
        if last and initials:
            return f"{initials}. {last}"
    return trimmed


def _pick_focus(categories: set[str]) -> str:
    if not categories:
        return "Interdisciplinary research"
    unique = sorted(categories)[:2]
    return " · ".join(unique)


def build_network_from_papers(papers: list) -> list[NetworkNode]:
    """Build connection nodes from ResearchPaper ORM rows or dict-like objects."""

    researchers: dict[str, _ResearcherAgg] = {}
    institutions: dict[str, _InstitutionAgg] = {}

    for paper in papers:
        title = getattr(paper, "title", paper.get("title", ""))
        paper_id = getattr(paper, "id", paper.get("id", ""))
        authors = getattr(paper, "authors", paper.get("authors", ""))
        source = (getattr(paper, "source", paper.get("source", "")) or "Research network").strip()
        category = getattr(paper, "category", paper.get("category", ""))
        citations = int(getattr(paper, "citations", paper.get("citations", 0)) or 0)

        inst_id = f"inst-{_slugify(source)}"
        institution = institutions.get(inst_id)
        if institution is None:
            institution = _InstitutionAgg(name=source)
            institutions[inst_id] = institution
        institution.categories.add(category)
        institution.paper_ids.append(paper_id)
        institution.citations += citations
        if citations >= institution.top_citation:
            institution.top_citation = citations
            institution.featured_paper = FeaturedPaper(id=paper_id, title=title)

        for raw_author in _parse_author_names(authors):
            name = _format_author_name(raw_author)
            researcher_id = f"researcher-{_slugify(name)}"
            researcher = researchers.get(researcher_id)
            if researcher is None:
                researcher = _ResearcherAgg(name=name)
                researchers[researcher_id] = researcher
            researcher.sources.add(source)
            researcher.categories.add(category)
            researcher.paper_ids.append(paper_id)
            researcher.citations += citations
            if citations >= researcher.top_citation:
                researcher.top_citation = citations
                researcher.featured_paper = FeaturedPaper(id=paper_id, title=title)

    researcher_nodes = [
        NetworkNode(
            id=node_id,
            kind="researcher",
            name=data.name,
            subtitle=" · ".join(sorted(data.sources)[:2]) or "Independent researcher",
            focus=_pick_focus(data.categories),
            paper_count=len(data.paper_ids),
            citations=data.citations,
            paper_ids=data.paper_ids,
            featured_paper=data.featured_paper,
        )
        for node_id, data in researchers.items()
    ]
    researcher_nodes.sort(key=lambda n: n.citations, reverse=True)

    institution_nodes = [
        NetworkNode(
            id=node_id,
            kind="institution",
            name=data.name,
            subtitle=f"{len(data.paper_ids)} papers in library",
            focus=_pick_focus(data.categories),
            paper_count=len(data.paper_ids),
            citations=data.citations,
            paper_ids=data.paper_ids,
            featured_paper=data.featured_paper,
        )
        for node_id, data in institutions.items()
    ]
    institution_nodes.sort(key=lambda n: n.paper_count, reverse=True)

    return researcher_nodes + institution_nodes
