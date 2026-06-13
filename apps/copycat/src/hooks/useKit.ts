/**
 * useKit — paired desktop kit status, permissions, adaptive stream config.
 * Data stays local on the kit machine; API only relays signed RPC.
 */
import { useCallback, useEffect, useState } from "react";
import { useCopycatAuth } from "../context/AuthContext";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface KitPermissions {
  ready?: boolean;
  screen_capture?: boolean;
  mouse_keyboard?: boolean;
  platform?: string;
  backend?: string;
  rust?: boolean;
  hints?: string[];
}

export interface KitDevice {
  id: string;
  name: string;
  is_online: boolean;
  last_seen_at?: string | null;
}

export interface StreamConfig {
  min_fps?: number;
  max_fps?: number;
  min_quality?: number;
  max_quality?: number;
  min_scale?: number;
  max_scale?: number;
  focus_mode?: boolean;
  target_latency_ms?: number;
}

export function useKit() {
  const { token } = useCopycatAuth();
  const [devices, setDevices] = useState<KitDevice[]>([]);
  const [permissions, setPermissions] = useState<KitPermissions | null>(null);
  const [kitOnline, setKitOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pairCode, setPairCode] = useState<string | null>(null);
  const [streamStats, setStreamStats] = useState<Record<string, unknown> | null>(null);

  const headers = useCallback((): HeadersInit => {
    const h: HeadersInit = { "Content-Type": "application/json" };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  }, [token]);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [devRes, permRes] = await Promise.all([
        fetch(`${API_BASE}/api/kit/devices`, { headers: headers() }),
        fetch(`${API_BASE}/api/kit/permissions`, { headers: headers() }),
      ]);
      if (devRes.ok) {
        const data = await devRes.json();
        const list: KitDevice[] = data.devices || [];
        setDevices(list);
        setKitOnline(list.some((d) => d.is_online));
      }
      if (permRes.ok) {
        setPermissions(await permRes.json());
      }
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const generatePairCode = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/kit/pair/code`, {
      method: "POST",
      headers: headers(),
    });
    if (!res.ok) return null;
    const data = await res.json();
    setPairCode(data.code);
    return data.code as string;
  }, [headers]);

  const configureStream = useCallback(
    async (config: StreamConfig) => {
      const res = await fetch(`${API_BASE}/api/kit/stream/configure`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ ...config }),
      });
      if (res.ok) {
        const data = await res.json();
        setStreamStats(data);
        return data;
      }
      return null;
    },
    [headers]
  );

  const enableFocusCapture = useCallback(async () => {
    return configureStream({ focus_mode: true });
  }, [configureStream]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, [refresh]);

  return {
    devices,
    permissions,
    kitOnline,
    loading,
    pairCode,
    streamStats,
    refresh,
    generatePairCode,
    configureStream,
    enableFocusCapture,
  };
}
