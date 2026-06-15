import { getAuthHeaders } from "./api";
import type {
  ConnectionConversation,
  ConnectionKind,
  ConnectionMessage,
  ConnectionStatus,
  MessageType,
  ResearchConnection,
} from "../pages/connections/types";

const API_BASE = import.meta.env.VITE_API_URL || "";

function apiUrl(path: string): string {
  return `${API_BASE.replace(/\/$/, "")}${path}`;
}

export interface ApiFeaturedPaper {
  id: string;
  title: string;
}

export interface ApiNetworkConnection {
  id: string;
  kind: ConnectionKind;
  name: string;
  subtitle: string;
  focus: string;
  paper_count: number;
  citations: number;
  paper_ids: string[];
  featured_paper?: ApiFeaturedPaper | null;
  status: ConnectionStatus;
}

export interface ApiNetworkStats {
  researchers: number;
  institutions: number;
  connected: number;
}

export interface ApiNetworkListResponse {
  items: ApiNetworkConnection[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  stats: ApiNetworkStats;
}

export interface ApiCorrespondence {
  id: string;
  connection_id: string;
  subject: string;
  salutation: string;
  body: string;
  closing: string;
  purpose?: string | null;
  sent_at: string;
  direction: "outgoing" | "incoming";
  sender_name?: string | null;
  message_type: MessageType;
}

export interface ApiConversationPreview {
  target_id: string;
  kind: ConnectionKind;
  name: string;
  subtitle: string;
  focus: string;
  status: ConnectionStatus;
  last_message?: ApiCorrespondence | null;
  message_count: number;
}

export interface CorrespondenceInput {
  subject?: string;
  salutation?: string;
  body: string;
  closing?: string;
  purpose?: string;
  message_type?: MessageType;
}

export function mapNetworkConnection(item: ApiNetworkConnection): ResearchConnection & { status: ConnectionStatus } {
  return {
    id: item.id,
    kind: item.kind,
    name: item.name,
    subtitle: item.subtitle,
    focus: item.focus,
    paperCount: item.paper_count,
    citations: item.citations,
    paperIds: item.paper_ids,
    featuredPaper: item.featured_paper
      ? { id: item.featured_paper.id, title: item.featured_paper.title }
      : undefined,
    status: item.status,
  };
}

export function mapCorrespondence(item: ApiCorrespondence): ConnectionMessage {
  return {
    id: item.id,
    connectionId: item.connection_id,
    subject: item.subject,
    salutation: item.salutation,
    body: item.body,
    closing: item.closing,
    purpose: item.purpose ?? undefined,
    sentAt: item.sent_at,
    direction: item.direction,
    senderName: item.sender_name ?? undefined,
    messageType: item.message_type,
  };
}

export function mapConversation(item: ApiConversationPreview): ConnectionConversation {
  return {
    targetId: item.target_id,
    kind: item.kind,
    name: item.name,
    subtitle: item.subtitle,
    focus: item.focus,
    status: item.status,
    lastMessage: item.last_message ? mapCorrespondence(item.last_message) : undefined,
    messageCount: item.message_count,
  };
}

async function authRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
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

async function optionalAuthRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = { ...getAuthHeaders(), ...(init?.headers || {}) };
  const res = await fetch(apiUrl(path), { ...init, headers });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const connectionsApi = {
  listNetwork(params?: {
    q?: string;
    kind?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.kind && params.kind !== "all") qs.set("kind", params.kind);
    if (params?.status === "connected") qs.set("status", "connected");
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return optionalAuthRequest<ApiNetworkListResponse>(`/api/connections/network${q ? `?${q}` : ""}`);
  },

  listConversations() {
    return authRequest<ApiConversationPreview[]>("/api/connections/conversations");
  },

  requestConnection(targetId: string) {
    return authRequest<{ target_id: string; status: ConnectionStatus }>(
      `/api/connections/${encodeURIComponent(targetId)}/request`,
      { method: "POST" },
    );
  },

  acceptConnection(targetId: string) {
    return authRequest<{ target_id: string; status: ConnectionStatus }>(
      `/api/connections/${encodeURIComponent(targetId)}/accept`,
      { method: "POST" },
    );
  },

  removeConnection(targetId: string) {
    return authRequest<void>(`/api/connections/${encodeURIComponent(targetId)}`, { method: "DELETE" });
  },

  listMessages(targetId: string) {
    return authRequest<ApiCorrespondence[]>(
      `/api/connections/${encodeURIComponent(targetId)}/messages`,
    );
  },

  sendMessage(targetId: string, payload: CorrespondenceInput) {
    return authRequest<ApiCorrespondence[]>(
      `/api/connections/${encodeURIComponent(targetId)}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
  },

  summary() {
    return authRequest<ApiNetworkStats>("/api/connections/me/summary");
  },
};
