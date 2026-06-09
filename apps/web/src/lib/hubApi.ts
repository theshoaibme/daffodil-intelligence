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
  return res.json();
}

export interface SkillRecord {
  id: string;
  name: string;
  description: string;
  content: string;
  tool_names?: string[];
  source?: string;
  recording_name?: string | null;
  tags?: string[];
  is_public?: boolean;
  usage_count?: number;
  created_at?: number;
}

export interface SkillHubResponse {
  count: number;
  public_count: number;
  copycat_count: number;
  total: number;
  limit: number;
  offset: number;
  skills: SkillRecord[];
}

export interface AgentHubRecord {
  id: string;
  name: string;
  description?: string;
  kind: "builtin" | "custom";
  category: string;
  tools?: string[];
  tool_count?: number;
  skill_count?: number;
  status?: string;
  is_public?: boolean;
  usage_count?: number;
  rating?: number;
  created_by?: number;
  system_prompt?: string;
  personality?: Record<string, unknown>;
  capabilities?: Record<string, unknown>[];
  profile?: {
    agent_id: string;
    skill_ids: string[];
    ruleset_ids: string[];
    extra_system: string;
  };
}

export interface AgentProfileConfig {
  agent_id: string;
  skill_ids: string[];
  ruleset_ids: string[];
  extra_system: string;
}

export interface GlobalConfig {
  ruleset_ids: string[];
  skill_ids: string[];
  extra_system: string;
  default_agent_id: string;
}

export const hubApi = {
  listSkills(params?: { tag?: string; source?: string; q?: string; limit?: number; offset?: number }) {
    const qs = new URLSearchParams();
    if (params?.tag) qs.set("tag", params.tag);
    if (params?.source) qs.set("source", params.source);
    if (params?.q) qs.set("q", params.q);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const query = qs.toString();
    return request<SkillHubResponse>(`/api/skills/hub${query ? `?${query}` : ""}`);
  },

  createSkill(body: Partial<SkillRecord> & { name: string; description: string; content: string }) {
    return request<SkillRecord>("/api/skills/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  updateSkill(id: string, body: Partial<SkillRecord>) {
    return request<SkillRecord>(`/api/skills/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  deleteSkill(id: string) {
    return request<{ status: string }>(`/api/skills/${id}`, { method: "DELETE" });
  },

  getGlobalConfig() {
    return request<GlobalConfig>("/api/skills/config/global");
  },

  putGlobalConfig(body: Partial<GlobalConfig>) {
    return request<GlobalConfig>("/api/skills/config/global", {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  getAgentProfile(agentId: string) {
    return request<AgentProfileConfig>(`/api/skills/config/agent/${agentId}`);
  },

  putAgentProfile(agentId: string, body: Partial<AgentProfileConfig>) {
    return request<AgentProfileConfig>(`/api/skills/config/agent/${agentId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  listAgents(params?: { kind?: string; category?: string; q?: string }) {
    const qs = new URLSearchParams();
    if (params?.kind) qs.set("kind", params.kind);
    if (params?.category) qs.set("category", params.category);
    if (params?.q) qs.set("q", params.q);
    const query = qs.toString();
    return request<{ agents: AgentHubRecord[]; count: number }>(
      `/api/agents/hub${query ? `?${query}` : ""}`
    );
  },

  getAgent(id: string) {
    return request<AgentHubRecord>(`/api/agents/hub/${id}`);
  },

  createAgent(body: {
    name: string;
    description: string;
    category?: string;
    template?: string;
    custom_prompt?: string;
    system_prompt?: string;
    capabilities?: { name: string; description?: string; tools?: string[]; enabled?: boolean }[];
    skill_ids?: string[];
    ruleset_ids?: string[];
    is_public?: boolean;
  }) {
    return request<AgentHubRecord>("/api/agents/hub", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  updateAgent(id: string, body: Record<string, unknown>) {
    return request<AgentHubRecord>(`/api/agents/hub/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  deleteAgent(id: string) {
    return request<{ status: string }>(`/api/agents/hub/${id}`, { method: "DELETE" });
  },
};
