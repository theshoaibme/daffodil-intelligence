import {
  clearAuthSession,
  persistAuthSession,
  readStoredToken,
} from "./authSession";
import type { ChatContextUsage } from "./chatContext";

const API_BASE = import.meta.env.VITE_API_URL || "";

function apiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  return `${base}${path}`;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

let unauthorizedHandler: (() => void) | null = null;

export function registerUnauthorizedHandler(handler: () => void) {
  unauthorizedHandler = handler;
}

export function getAuthHeaders(): HeadersInit {
  const token = readStoredToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      const messages = data.detail.map((d: { msg?: string; loc?: (string | number)[] }) => {
        const field = d.loc?.filter((part) => typeof part === "string" && part !== "body").pop();
        const label = field === "semester" ? "Semester" : field;
        const msg = d.msg ?? "";
        if (label === "semester" && msg.includes("less than or equal")) {
          return "Batch ID must be between 1 and 999.";
        }
        return label ? `${label}: ${msg}` : msg;
      });
      return messages.filter(Boolean).join(", ") || res.statusText;
    }
    return data.message || res.statusText;
  } catch {
    return res.statusText || "Request failed";
  }
}

async function authFetch(
  url: string,
  init?: RequestInit,
  notifyUnauthorized = true
): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        ...getAuthHeaders(),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError("Unable to reach the server. Check your connection.", 0);
  }

  if (notifyUnauthorized && (response.status === 401 || response.status === 403)) {
    unauthorizedHandler?.();
  }

  return response;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  student_id?: string | null;
  department?: string | null;
  semester?: number | null;
  avatar_url?: string | null;
  created_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(apiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function register(data: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<UserResponse> {
  const res = await fetch(apiUrl("/api/auth/register"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function sendRegisterOtp(data: {
  email: string;
  accept_terms: boolean;
}): Promise<{ message: string; email: string; dev_otp?: string }> {
  const res = await fetch(apiUrl("/api/auth/register/send-otp"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function verifyRegisterOtp(data: {
  email: string;
  code: string;
}): Promise<{ message: string; email: string }> {
  const res = await fetch(apiUrl("/api/auth/register/verify-otp"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function completeRegister(data: {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  role: "student" | "teacher" | "staff" | "manager";
}): Promise<UserResponse> {
  const res = await fetch(apiUrl("/api/auth/register/complete"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function refreshAccessToken(): Promise<LoginResponse> {
  const res = await authFetch(apiUrl("/api/auth/refresh"), { method: "POST" }, false);
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  const data = (await res.json()) as LoginResponse;
  persistAuthSession(data.access_token, null);
  return data;
}

export async function fetchCurrentUser(): Promise<UserResponse> {
  const res = await authFetch(apiUrl("/api/auth/me"), undefined, false);
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export interface UserUpdatePayload {
  full_name?: string | null;
  student_id?: string | null;
  department?: string | null;
  semester?: number | null;
  avatar_url?: string | null;
}

export async function updateCurrentUser(data: UserUpdatePayload): Promise<UserResponse> {
  const res = await authFetch(apiUrl("/api/auth/me"), {
    method: "PATCH",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<{ message: string }> {
  const res = await authFetch(apiUrl("/api/auth/account/password"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export const DELETE_ACCOUNT_PHRASE = "Delete my account";

export async function deleteAccount(payload: {
  confirmation_phrase: string;
}): Promise<{ message: string }> {
  const res = await authFetch(apiUrl("/api/auth/account/delete"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function fetchGoogleOAuthConfig(): Promise<{
  enabled: boolean;
  client_id: string | null;
  redirect_uri?: string;
}> {
  const res = await fetch(apiUrl("/api/auth/oauth/google/config"));
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export function googleOAuthStartUrl(): string {
  return apiUrl("/api/auth/oauth/google/start");
}

export async function exchangeGoogleCode(code: string, redirectUri: string): Promise<{
  access_token: string;
  user?: Record<string, unknown>;
}> {
  const res = await fetch(apiUrl("/api/auth/oauth/google"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, redirect_uri: redirectUri }),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export interface ChatResponse {
  id: number;
  title: string;
  agent_type: string;
}

export async function fetchChatContextUsage(
  chatId: number,
  draft = "",
  modelId?: string
): Promise<ChatContextUsage> {
  const params = new URLSearchParams();
  if (draft.trim()) params.set("draft", draft.trim());
  if (modelId) params.set("model_id", modelId);
  const qs = params.toString();
  const res = await authFetch(
    apiUrl(`/api/chats/${chatId}/context${qs ? `?${qs}` : ""}`)
  );
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function createChat(agentType: string): Promise<ChatResponse> {
  const res = await authFetch(apiUrl("/api/chats/"), {
    method: "POST",
    body: JSON.stringify({ title: "New Chat", agent_type: agentType }),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

interface StreamResult {
  content: string;
  metadata?: Record<string, unknown>;
}

export interface StreamEvent {
  type: "thinking" | "tool" | "agent" | "subagent" | "status" | "model";
  content?: string;
  name?: string;
  status?: string;
  agent_id?: string;
}

async function consumeSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onChunk?: (text: string) => void,
  onContext?: (context: ChatContextUsage) => void,
  onEvent?: (event: StreamEvent) => void
): Promise<StreamResult> {
  const decoder = new TextDecoder();
  let buffer = "";
  let fullContent = "";
  let metadata: Record<string, unknown> | undefined;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line.startsWith("data:")) continue;

      const payload = line.slice(5).trim();
      if (!payload || payload === "[DONE]") continue;

      try {
        const parsed = JSON.parse(payload) as {
          type?: string;
          content?: string;
          id?: number;
          role?: string;
          metadata?: Record<string, unknown>;
          model_id?: string;
          model_mode?: string;
          model_routing?: string;
          usage_ratio?: number;
          used_tokens?: number;
          max_tokens?: number;
          usage_percent?: number;
          breakdown?: ChatContextUsage["breakdown"];
          message_count?: number;
          name?: string;
          status?: string;
          agent_id?: string;
        };

        if (parsed.type === "context" && parsed.usage_ratio != null) {
          const ctx: ChatContextUsage = {
            usage_ratio: parsed.usage_ratio,
            used_tokens: parsed.used_tokens ?? 0,
            max_tokens: parsed.max_tokens ?? 128_000,
            usage_percent: parsed.usage_percent ?? 0,
            breakdown: parsed.breakdown ?? {
              messages: 0,
              draft: 0,
              memory_recall: 0,
              system_overhead: 0,
            },
            message_count: parsed.message_count ?? 0,
            model_id: parsed.model_id,
          };
          metadata = { ...metadata, context_usage: ctx };
          onContext?.(ctx);
          continue;
        }

        if (parsed.type === "model") {
          metadata = {
            ...metadata,
            model_id: parsed.model_id,
            model_mode: parsed.model_mode,
            model_routing: parsed.model_routing,
          };
          onEvent?.({
            type: "model",
            content: parsed.model_id,
            name: parsed.model_routing,
          });
          continue;
        }

        if (parsed.type === "status") {
          if (parsed.content) onEvent?.({ type: "status", content: parsed.content });
          continue;
        }

        if (parsed.type === "thinking") {
          if (parsed.content) onEvent?.({ type: "thinking", content: parsed.content });
          continue;
        }

        if (parsed.type === "tool") {
          onEvent?.({ type: "tool", name: parsed.name, status: parsed.status });
          continue;
        }

        if (parsed.type === "agent" || parsed.type === "subagent") {
          onEvent?.({
            type: parsed.type,
            name: parsed.name,
            status: parsed.status,
            agent_id: parsed.agent_id,
            content: parsed.content,
          });
          continue;
        }

        if (typeof parsed.content !== "string") continue;

        if (parsed.id != null && parsed.role === "assistant") {
          fullContent = parsed.content;
          metadata = parsed.metadata;
          continue;
        }

        fullContent += parsed.content;
        onChunk?.(parsed.content);
      } catch {
        // Ignore malformed SSE JSON lines.
      }
    }
  }

  return { content: fullContent, metadata };
}

export async function sendMessage(
  chatId: number,
  content: string,
  onChunk?: (chunk: string) => void,
  modelId?: string,
  onContext?: (context: ChatContextUsage) => void,
  metadata?: Record<string, unknown>,
  onEvent?: (event: StreamEvent) => void
): Promise<{ content: string; metadata?: Record<string, unknown> }> {
  const res = await authFetch(apiUrl(`/api/chats/${chatId}/messages`), {
    method: "POST",
    body: JSON.stringify({
      content,
      model_id: modelId,
      metadata: metadata ?? {},
    }),
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("text/event-stream") || contentType.includes("application/x-ndjson")) {
    const reader = res.body?.getReader();
    if (!reader) throw new Error("No response body");
    return consumeSSEStream(reader, onChunk, onContext, onEvent);
  }

  const data = await res.json();
  const text = data.response ?? data.content ?? "";
  onChunk?.(text);
  return { content: text, metadata: data.metadata };
}

export { clearAuthSession };
