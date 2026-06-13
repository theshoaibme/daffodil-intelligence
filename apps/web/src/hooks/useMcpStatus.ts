import { useCallback, useEffect, useState } from "react";
import {
  fetchMcpStatusDetail,
  fetchMcpUserServers,
  saveMcpUserServers,
  testDaffodilMcpServer,
  testMcpServer,
  validateMcpServer,
  type McpServerTestResult,
  type McpStatusDetail,
  type McpValidationResult,
} from "../lib/mcpApi";
import {
  readLocalMcpServers,
  saveLocalMcpServers,
  type LocalMcpServer,
} from "../lib/mcpConfig";

export interface McpStatus {
  status: string;
  enabled: boolean;
  sdk_available: boolean;
  antigravity_available?: boolean;
  configured: boolean;
  server_count: number;
  transport: string;
  servers: string[];
  local_tool_count?: number;
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

function toMenuStatus(detail: McpStatusDetail): McpStatus {
  const names = detail.servers.map((server) => server.name);
  return {
    status: detail.status,
    enabled: detail.enabled,
    sdk_available: detail.sdk_available,
    antigravity_available: detail.antigravity_available,
    configured: detail.configured,
    server_count: detail.server_count,
    transport: detail.transport,
    servers: names,
    local_tool_count: detail.local_tool_count,
    has_external_env: detail.server_count > 0,
  };
}

function syncLocalToUserServers(servers: LocalMcpServer[]) {
  return saveMcpUserServers(
    servers.map((server) => ({ name: server.name, command: server.command }))
  ).catch(() => null);
}

export function useMcpStatus(pollMs = 8000) {
  const [status, setStatus] = useState<McpStatus>(DEFAULT_STATUS);
  const [detail, setDetail] = useState<McpStatusDetail | null>(null);
  const [localServers, setLocalServers] = useState(readLocalMcpServers);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const refreshLocal = useCallback(() => {
    setLocalServers(readLocalMcpServers());
  }, []);

  const updateLocalServers = useCallback((servers: LocalMcpServer[]) => {
    saveLocalMcpServers(servers);
    setLocalServers(servers);
    setSyncing(true);
    void syncLocalToUserServers(servers).finally(() => setSyncing(false));
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const [menuRes, detailRes] = await Promise.all([
        fetch(apiUrl("/api/system/mcp")).then(async (res) => {
          if (!res.ok) throw new Error("status failed");
          return (await res.json()) as McpStatus;
        }),
        fetchMcpStatusDetail(),
      ]);
      setStatus({ ...DEFAULT_STATUS, ...menuRes });
      setDetail(detailRes);
    } catch {
      try {
        const detailRes = await fetchMcpStatusDetail();
        setDetail(detailRes);
        setStatus(toMenuStatus(detailRes));
      } catch {
        setStatus(DEFAULT_STATUS);
        setDetail(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUserServers = useCallback(async () => {
    try {
      const remote = await fetchMcpUserServers();
      if (remote.servers.length > 0) {
        const mapped: LocalMcpServer[] = remote.servers.map((server, index) => ({
          id: `remote-${index}-${server.name}`,
          name: server.name,
          command: server.command,
        }));
        saveLocalMcpServers(mapped);
        setLocalServers(mapped);
        return;
      }
    } catch {
      // fall back to browser storage
    }
    refreshLocal();
  }, [refreshLocal]);

  useEffect(() => {
    void loadUserServers();
    void fetchStatus();
    const interval = window.setInterval(fetchStatus, pollMs);
    return () => window.clearInterval(interval);
  }, [fetchStatus, loadUserServers, pollMs]);

  const validateServer = useCallback(
    (name: string, command: string): Promise<McpValidationResult> =>
      validateMcpServer(name, command),
    []
  );

  const testServer = useCallback(
    (name: string, command: string): Promise<McpServerTestResult> =>
      testMcpServer(name, command),
    []
  );

  const testSelf = useCallback(
    (): Promise<McpServerTestResult> => testDaffodilMcpServer(),
    []
  );

  const isConfigured = status.configured || localServers.length > 0;

  return {
    status,
    detail,
    loading,
    syncing,
    localServers,
    isConfigured,
    refetch: fetchStatus,
    refreshLocal,
    updateLocalServers,
    loadUserServers,
    validateServer,
    testServer,
    testSelf,
  };
}
