import { useCallback, useEffect, useRef, useState } from "react";
import { connectionsApi, mapCorrespondence, mapNetworkConnection } from "@lib/connectionsApi";
import type { ConnectionMessage, ConnectionStatus, ResearchConnection } from "../types";

export type ResearchConnectionWithStatus = ResearchConnection & { status: ConnectionStatus };

const NETWORK_PAGE_LIMIT = 200;

interface NetworkStats {
  researchers: number;
  institutions: number;
  connected: number;
}

export function useConnectionsNetwork(isAuthenticated: boolean) {
  const [connections, setConnections] = useState<ResearchConnectionWithStatus[]>([]);
  const [stats, setStats] = useState<NetworkStats>({ researchers: 0, institutions: 0, connected: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [messageCache, setMessageCache] = useState<Record<string, ConnectionMessage[]>>({});
  const requestIdRef = useRef(0);

  const refresh = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    try {
      const items: ResearchConnectionWithStatus[] = [];
      let page = 1;
      let totalPages = 1;
      let networkStats: NetworkStats = { researchers: 0, institutions: 0, connected: 0 };

      while (page <= totalPages) {
        const res = await connectionsApi.listNetwork({ limit: NETWORK_PAGE_LIMIT, page });
        if (requestId !== requestIdRef.current) return;

        items.push(...res.items.map(mapNetworkConnection));
        networkStats = res.stats;
        totalPages = Math.max(1, res.total_pages ?? 1);

        if (page >= totalPages || !res.items.length) break;
        page += 1;
      }

      setConnections(items);
      setStats(networkStats);
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setConnections([]);
      setStats({ researchers: 0, institutions: 0, connected: 0 });
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
  }, [refresh, isAuthenticated]);

  const getStatus = useCallback(
    (connectionId: string): ConnectionStatus => {
      return connections.find((c) => c.id === connectionId)?.status ?? "available";
    },
    [connections],
  );

  const patchStatus = useCallback((connectionId: string, status: ConnectionStatus) => {
    setConnections((prev) => {
      const next = prev.map((c) => (c.id === connectionId ? { ...c, status } : c));
      setStats((s) => ({
        ...s,
        connected: next.filter((c) => c.status === "connected").length,
      }));
      return next;
    });
  }, []);

  const connect = useCallback(
    async (connectionId: string) => {
      if (!isAuthenticated) return;
      const res = await connectionsApi.requestConnection(connectionId);
      patchStatus(connectionId, res.status);
    },
    [isAuthenticated, patchStatus],
  );

  const acceptConnection = useCallback(
    async (connectionId: string) => {
      if (!isAuthenticated) return;
      const res = await connectionsApi.acceptConnection(connectionId);
      patchStatus(connectionId, res.status);
    },
    [isAuthenticated, patchStatus],
  );

  const loadMessages = useCallback(
    async (connectionId: string) => {
      if (!isAuthenticated) return [];
      const rows = await connectionsApi.listMessages(connectionId);
      const mapped = rows.map(mapCorrespondence);
      setMessageCache((prev) => ({ ...prev, [connectionId]: mapped }));
      return mapped;
    },
    [isAuthenticated],
  );

  const sendMessage = useCallback(
    async (
      connectionId: string,
      payload: {
        subject: string;
        salutation: string;
        body: string;
        closing: string;
        purpose?: string;
      },
    ) => {
      if (!isAuthenticated) return;
      const created = await connectionsApi.sendMessage(connectionId, payload);
      const mapped = mapCorrespondence(created);
      setMessageCache((prev) => ({
        ...prev,
        [connectionId]: [...(prev[connectionId] ?? []), mapped],
      }));
      patchStatus(connectionId, "pending");
    },
    [isAuthenticated, patchStatus],
  );

  const getMessages = useCallback(
    (connectionId: string) => messageCache[connectionId] ?? [],
    [messageCache],
  );

  return {
    connections,
    stats,
    loading,
    error,
    refresh,
    getStatus,
    connect,
    acceptConnection,
    sendMessage,
    loadMessages,
    getMessages,
    connectedCount: stats.connected,
  };
}
