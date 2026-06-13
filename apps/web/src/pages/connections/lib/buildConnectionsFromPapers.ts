import type { ResearchPaper } from "../../research/components/types";
import type { ConnectionKind, ResearchConnection } from "../types";

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function parseAuthorNames(authors: string): string[] {
  const cleaned = authors
    .replace(/\([^)]*\)/g, "")
    .replace(/\bet al\.?\b/gi, "")
    .trim();

  return cleaned
    .split(/,|&|\band\b/gi)
    .map((part) => part.trim())
    .filter((part) => part.length > 1 && !/^(jr|sr|phd|md)$/i.test(part))
    .slice(0, 4);
}

function formatAuthorName(raw: string): string {
  const trimmed = raw.trim();
  if (trimmed.includes(".")) {
    const [last, ...rest] = trimmed.split(",").map((s) => s.trim());
    if (last && rest.length) {
      const initials = rest.join(" ").replace(/\./g, "").trim();
      return initials ? `${initials}. ${last}` : last;
    }
  }
  return trimmed;
}

function pickFocus(categories: string[]): string {
  if (!categories.length) return "Interdisciplinary research";
  const unique = [...new Set(categories)];
  return unique.slice(0, 2).join(" · ");
}

export function buildConnectionsFromPapers(papers: ResearchPaper[]): ResearchConnection[] {
  const researchers = new Map<
    string,
    {
      name: string;
      sources: Set<string>;
      categories: Set<string>;
      paperIds: string[];
      citations: number;
      topCitation: number;
      featuredPaper?: { id: string; title: string };
    }
  >();

  const institutions = new Map<
    string,
    {
      name: string;
      categories: Set<string>;
      paperIds: string[];
      citations: number;
      topCitation: number;
      featuredPaper?: { id: string; title: string };
    }
  >();

  for (const paper of papers) {
    const source = paper.source?.trim() || "Research network";
    const institutionId = `inst-${slugify(source)}`;
    const institution = institutions.get(institutionId) ?? {
      name: source,
      categories: new Set<string>(),
      paperIds: [],
      citations: 0,
      topCitation: 0,
      featuredPaper: undefined,
    };
    institution.categories.add(paper.category);
    institution.paperIds.push(paper.id);
    institution.citations += paper.citations;
    if (paper.citations >= institution.topCitation) {
      institution.topCitation = paper.citations;
      institution.featuredPaper = { id: paper.id, title: paper.title };
    }
    institutions.set(institutionId, institution);

    for (const rawAuthor of parseAuthorNames(paper.authors)) {
      const name = formatAuthorName(rawAuthor);
      const id = `researcher-${slugify(name)}`;
      const researcher = researchers.get(id) ?? {
        name,
        sources: new Set<string>(),
        categories: new Set<string>(),
        paperIds: [],
        citations: 0,
        topCitation: 0,
        featuredPaper: undefined,
      };
      researcher.sources.add(source);
      researcher.categories.add(paper.category);
      researcher.paperIds.push(paper.id);
      researcher.citations += paper.citations;
      if (paper.citations >= researcher.topCitation) {
        researcher.topCitation = paper.citations;
        researcher.featuredPaper = { id: paper.id, title: paper.title };
      }
      researchers.set(id, researcher);
    }
  }

  const researcherConnections: ResearchConnection[] = [...researchers.entries()]
    .map(([id, data]) => ({
      id,
      kind: "researcher" as ConnectionKind,
      name: data.name,
      subtitle: [...data.sources].slice(0, 2).join(" · ") || "Independent researcher",
      focus: pickFocus([...data.categories]),
      paperCount: data.paperIds.length,
      citations: data.citations,
      paperIds: data.paperIds,
      featuredPaper: data.featuredPaper,
    }))
    .sort((a, b) => b.citations - a.citations);

  const institutionConnections: ResearchConnection[] = [...institutions.entries()]
    .map(([id, data]) => ({
      id,
      kind: "institution" as ConnectionKind,
      name: data.name,
      subtitle: `${data.paperIds.length} papers in library`,
      focus: pickFocus([...data.categories]),
      paperCount: data.paperIds.length,
      citations: data.citations,
      paperIds: data.paperIds,
      featuredPaper: data.featuredPaper,
    }))
    .sort((a, b) => b.paperCount - a.paperCount);

  return [...researcherConnections, ...institutionConnections];
}
