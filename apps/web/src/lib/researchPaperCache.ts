import { mapResearchPaper, researchApi } from "./researchApi";
import type { ResearchPaper } from "../pages/research/components/types";

const CACHE_TTL_MS = 60_000;
const MAX_PAGES = 10;
const PAGE_LIMIT = 100;

let cachedPapers: ResearchPaper[] | null = null;
let cachedAt = 0;
let inflight: Promise<ResearchPaper[]> | null = null;

export function invalidatePublicResearchPaperCache(): void {
  cachedPapers = null;
  cachedAt = 0;
  inflight = null;
}

/** Fetch public papers once, with in-flight dedup + short TTL cache. */
export async function fetchPublicResearchPapers(opts?: {
  force?: boolean;
  maxPages?: number;
}): Promise<ResearchPaper[]> {
  const force = opts?.force ?? false;
  const maxPages = opts?.maxPages ?? MAX_PAGES;
  const now = Date.now();

  if (!force && cachedPapers && now - cachedAt < CACHE_TTL_MS) {
    return cachedPapers;
  }

  if (!force && inflight) {
    return inflight;
  }

  inflight = (async () => {
    const items: ResearchPaper[] = [];
    let page = 1;
    let totalPages = 1;

    while (page <= totalPages && page <= maxPages) {
      const res = await researchApi.listPublic({ limit: PAGE_LIMIT, page });
      if (!res.items.length) break;

      items.push(...res.items.map(mapResearchPaper));
      totalPages = Math.max(1, res.total_pages ?? 1);

      if (page >= totalPages) break;
      page += 1;
    }

    cachedPapers = items;
    cachedAt = Date.now();
    return items;
  })();

  try {
    return await inflight;
  } catch (err) {
    invalidatePublicResearchPaperCache();
    throw err;
  } finally {
    inflight = null;
  }
}

/** Lightweight fetch for connection graph — first page only. */
export async function fetchPublicResearchPapersForConnections(
  force = false,
): Promise<ResearchPaper[]> {
  const now = Date.now();
  if (!force && cachedPapers && now - cachedAt < CACHE_TTL_MS) {
    return cachedPapers;
  }

  if (!force && inflight) {
    return inflight;
  }

  inflight = (async () => {
    const res = await researchApi.listPublic({ limit: PAGE_LIMIT, page: 1 });
    const items = res.items.map(mapResearchPaper);
    cachedPapers = items;
    cachedAt = Date.now();
    return items;
  })();

  try {
    return await inflight;
  } catch (err) {
    invalidatePublicResearchPaperCache();
    throw err;
  } finally {
    inflight = null;
  }
}
