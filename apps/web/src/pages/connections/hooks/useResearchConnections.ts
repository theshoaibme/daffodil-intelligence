import { useCallback, useEffect, useState } from "react";
import { mapResearchPaper, researchApi } from "@lib";
import type { ResearchPaper } from "../../research/components/types";
import { buildConnectionsFromPapers } from "../lib/buildConnectionsFromPapers";
import type { ResearchConnection } from "../types";

export function useResearchConnections() {
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [connections, setConnections] = useState<ResearchConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items: ResearchPaper[] = [];
      let page = 1;
      let totalPages = 1;

      do {
        const res = await researchApi.listPublic({ limit: 100, page });
        items.push(...res.items.map(mapResearchPaper));
        totalPages = res.total_pages;
        page += 1;
      } while (page <= totalPages);

      setPapers(items);
      setConnections(buildConnectionsFromPapers(items));
    } catch (err) {
      setPapers([]);
      setConnections([]);
      setError(err instanceof Error ? err.message : "Failed to load research network");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { papers, connections, loading, error, refresh };
}
