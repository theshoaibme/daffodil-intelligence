import { useCallback, useEffect, useState } from "react";
import { readLocalMcpServers } from "../lib/mcpConfig";

export interface McpStatus {
  status: string;
  enabled: boolean;
  sdk_available: boolean;
  configured: boolean;
  server_count: number;
  transport: string;
  servers: string[];
  has_external_env?: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL || "";

const DEFAULT_STATUS: McpStatus = {
  status: "needs_configuration",
  enabled: false,
  sdk_available: false,
  configured: false,
  server_count: 0,
  transport: "stdio",
  servers: [],
};

function apiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  return `${base}${path}`;
}

export function useMcpStatus(pollMs = 8000) {
  const [status, setStatus] = useState<McpStatus>(DEFAULT_STATUS);
  const [localServers, setLocalServers] = useState(readLocalMcpServers);
  const [loading, setLoading] = useState(true);

  const refreshLocal = useCallback(() => {
    setLocalServers(readLocalMcpServers());
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/api/system/mcp"));
      if (!res.ok) throw new Error("Failed to fetch MCP status");
      const data = (await res.json()) as McpStatus;
      setStatus({ ...DEFAULT_STATUS, ...data });
    } catch {
      setStatus(DEFAULT_STATUS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshLocal();
    fetchStatus();
    const interval = window.setInterval(fetchStatus, pollMs);
    return () => window.clearInterval(interval);
  }, [fetchStatus, pollMs, refreshLocal]);

  const isConfigured =
    status.configured || localServers.length > 0;

  return {
    status,
    loading,
    localServers,
    isConfigured,
    refetch: fetchStatus,
    refreshLocal,
  };
}
