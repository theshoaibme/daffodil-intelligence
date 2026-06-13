import { useCallback, useEffect, useRef, useState } from "react";
import { fetchPublicResearchPapersForConnections } from "@lib/researchPaperCache";
import { buildConnectionsFromPapers } from "../lib/buildConnectionsFromPapers";
import type { ResearchConnection } from "../types";
import type { ResearchPaper } from "../../research/components/types";

export function useResearchConnections() {
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [connections, setConnections] = useState<ResearchConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  const refresh = useCallback(async (force = false) => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    try {
      const items = await fetchPublicResearchPapersForConnections(force);
      if (requestId !== requestIdRef.current) return;

      setPapers(items);
      setConnections(buildConnectionsFromPapers(items));
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setPapers([]);
      setConnections([]);
      setError(err instanceof Error ? err.message : "Failed to load research network");
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    refresh();
    return () => {
      requestIdRef.current += 1;
    };
  }, [refresh]);

  return { papers, connections, loading, error, refresh };
}
