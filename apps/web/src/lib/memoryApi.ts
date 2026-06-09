import { getAuthHeaders, ApiError } from "./api";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface MemoryRecord {
  id: string;
  agent_id?: string;
  content: string;
  memory_type: string;
  created_at: string;
  visibility?: string;
  source?: string;
  payload?: any;
  metadata?: any;
}

export interface MemoryStats {
  total: number;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
  qdrant_available?: boolean;
}

async function request(path: string, options: RequestInit = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };
  
  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(data.detail || "Request failed", response.status);
  }
  
  return response.json();
}

export const memoryApi = {
  async list(opts: {
    agent_id?: string;
    memory_type?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<{ items: MemoryRecord[]; total: number }> {
    const params = new URLSearchParams();
    if (opts.agent_id) params.append("agent_id", opts.agent_id);
    if (opts.memory_type) params.append("memory_type", opts.memory_type);
    if (opts.limit) params.append("limit", String(opts.limit));
    if (opts.offset) params.append("offset", String(opts.offset));
    
    return request(`/api/memory?${params.toString()}`);
  },

  async stats(): Promise<MemoryStats> {
    return request("/api/memory/stats");
  },

  async context(agentId: string): Promise<{ agent_id: string; snapshots: MemoryRecord[] }> {
    return request(`/api/memory/context/${agentId}`);
  },

  async remember(payload: {
    text: string;
    agent_id: string;
    memory_type: string;
    visibility?: string;
    metadata?: any;
    payload?: any;
  }): Promise<{ stored: boolean; id: string }> {
    return request("/api/memory/remember", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async recall(
    query: string,
    opts: {
      agent_id?: string;
      memory_type?: string;
      k?: number;
    } = {}
  ): Promise<{ query: string; notes: MemoryRecord[]; count: number }> {
    const params = new URLSearchParams();
    params.append("query", query);
    if (opts.agent_id) params.append("agent_id", opts.agent_id);
    if (opts.memory_type) params.append("memory_type", opts.memory_type);
    if (opts.k) params.append("k", String(opts.k));

    return request(`/api/memory/recall?${params.toString()}`);
  },

  async delete(memoryId: string): Promise<{ deleted: boolean; id: string }> {
    return request(`/api/memory/${memoryId}`, {
      method: "DELETE",
    });
  },

  async clear(opts: {
    agent_id?: string;
    memory_type?: string;
    all?: boolean;
  } = {}): Promise<{ cleared: number }> {
    const params = new URLSearchParams();
    if (opts.agent_id) params.append("agent_id", opts.agent_id);
    if (opts.memory_type) params.append("memory_type", opts.memory_type);
    if (opts.all) params.append("all", String(opts.all));

    return request(`/api/memory?${params.toString()}`, {
      method: "DELETE",
    });
  },

  async consolidate(): Promise<any> {
    return request("/api/memory/consolidate", {
      method: "POST",
    });
  },
};
