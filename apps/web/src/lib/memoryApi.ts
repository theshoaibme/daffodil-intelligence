import { getAuthHeaders } from "./api";

const API_BASE = import.meta.env.VITE_API_URL || "";

function url(path: string): string {
  return `${API_BASE.replace(/\/$/, "")}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url(path), {
    ...init,
    headers: { ...getAuthHeaders(), ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export interface MemoryRecord {
  id: string;
  user_id: number;
  agent_id: string;
  scope: string;
  content: string;
  memory_type: string;
  visibility: string;
  source: string;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface MemoryListResponse {
  items: MemoryRecord[];
  total: number;
}

export interface MemoryStats {
  total: number;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
  qdrant_available: boolean;
}

export const memoryApi = {
  list(params?: {
    agent_id?: string;
    memory_type?: string;
    scope?: string;
    chat_id?: string;
    limit?: number;
    offset?: number;
  }) {
    const qs = new URLSearchParams();
    if (params?.agent_id) qs.set("agent_id", params.agent_id);
    if (params?.memory_type) qs.set("memory_type", params.memory_type);
    if (params?.scope) qs.set("scope", params.scope);
    if (params?.chat_id) qs.set("chat_id", params.chat_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<MemoryListResponse>(`/api/memory${q ? `?${q}` : ""}`);
  },

  stats() {
    return request<MemoryStats>("/api/memory/stats");
  },

  context(agentId: string) {
    return request<{ agent_id: string; snapshots: MemoryRecord[] }>(
      `/api/memory/context/${encodeURIComponent(agentId)}`
    );
  },

  remember(body: {
    text: string;
    agent_id?: string;
    memory_type?: string;
    visibility?: string;
    metadata?: Record<string, unknown>;
  }) {
    return request<{ stored: boolean; id: string }>("/api/memory/remember", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  recall(query: string, params?: { k?: number; agent_id?: string; memory_type?: string; chat_id?: string }) {
    const qs = new URLSearchParams({ query });
    if (params?.k) qs.set("k", String(params.k));
    if (params?.agent_id) qs.set("agent_id", params.agent_id);
    if (params?.memory_type) qs.set("memory_type", params.memory_type);
    if (params?.chat_id) qs.set("chat_id", params.chat_id);
    return request<{ query: string; notes: MemoryRecord[]; count: number }>(
      `/api/memory/recall?${qs}`
    );
  },

  delete(id: string) {
    return request<{ deleted: boolean; id: string }>(`/api/memory/${id}`, { method: "DELETE" });
  },

  clear(params?: { agent_id?: string; memory_type?: string; chat_id?: string; all?: boolean }) {
    const qs = new URLSearchParams();
    if (params?.agent_id) qs.set("agent_id", params.agent_id);
    if (params?.memory_type) qs.set("memory_type", params.memory_type);
    if (params?.chat_id) qs.set("chat_id", params.chat_id);
    if (params?.all) qs.set("all", "true");
    const q = qs.toString();
    return request<{ cleared: number }>(`/api/memory${q ? `?${q}` : ""}`, { method: "DELETE" });
  },

  consolidate() {
    return request<{ promoted: number }>("/api/memory/consolidate", { method: "POST" });
  },

  summarize(chatId: number) {
    return request<{ summarized: boolean; summary_id?: string }>(
      `/api/memory/summarize/${chatId}`,
      { method: "POST" }
    );
  },
};
