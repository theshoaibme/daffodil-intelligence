import { useCallback, useEffect, useState } from "react";
import { resolveModelName } from "../lib/models";

export interface RuntimeStatus {
  status: string;
  engine: string;
  model: string;
  runtime_status: string;
  tools_count: number;
  agents_count: number;
  telegram: { enabled?: boolean; status?: string };
  mcp: { enabled?: boolean; status?: string; configured?: boolean; server_count?: number };
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const DEFAULT_RUNTIME: RuntimeStatus = {
  status: "unknown",
  engine: "antigravity",
  model: "gemini-2.0-flash",
  runtime_status: "down",
  tools_count: 0,
  agents_count: 0,
  telegram: {},
  mcp: {},
};

export function formatModelLabel(modelId: string): string {
  return resolveModelName(modelId);
}

export function useRuntimeStatus(pollMs = 5000) {
  const [runtime, setRuntime] = useState<RuntimeStatus>(DEFAULT_RUNTIME);
  const [loading, setLoading] = useState(true);

  const fetchRuntime = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/system/runtime`);
      if (!res.ok) throw new Error("Failed to fetch runtime");
      const data = await res.json();
      setRuntime({ ...DEFAULT_RUNTIME, ...data });
    } catch {
      // Keep last known or defaults when API is unreachable.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuntime();
    const interval = window.setInterval(fetchRuntime, pollMs);
    return () => window.clearInterval(interval);
  }, [fetchRuntime, pollMs]);

  return { runtime, loading, refetch: fetchRuntime };
}
