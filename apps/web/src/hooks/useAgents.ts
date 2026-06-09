/**
 * useAgents — Hook for real-time agent status and management
 */
import { useState, useEffect, useCallback } from "react";
import { getAuthHeaders } from "../lib/api";

export interface Agent {
  id: string;
  name: string;
  description?: string;
  tools?: string[];
  status: "idle" | "thinking" | "executing" | "error";
  category: string;
  kind?: "builtin" | "custom";
  skill_count?: number;
  currentTask?: string;
  tasksCompleted: number;
  lastActive?: string;
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/** Strip trailing " Agent" from API names for card labels. */
export function formatAgentDisplayName(name: string): string {
  return (name || "").replace(/\s+Agent$/i, "").trim() || name;
}

export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agents/hub`, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error("Failed to fetch agents");
      const data = await res.json();
      setAgents(
        (data.agents || []).map((a: any) => ({
          ...a,
          name: formatAgentDisplayName(a.name || a.id),
          status: a.status || "idle",
          tasksCompleted: 0,
        }))
      );
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents]);

  return { agents, loading, error, refetch: fetchAgents };
}
