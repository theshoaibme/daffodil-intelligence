import {
  clearAuthSession,
  persistAuthSession,
  readStoredToken,
} from "./authSession";
import type { ChatContextUsage } from "./chatContext";
import { coerceUiBlock, mergeUiBlocks } from "./uiBlocks/coerce";
import type { UiBlock } from "./uiBlocks/types";
import { parseEnvelope, envelopeToStreamEvent } from "./aiEvents";
import { eventBus } from "../engine/EventBus";
import type { AiEventEnvelope } from "../engine/types";

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
  created_at: string;
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

export interface ApiMessage {
  id: number;
  role: string;
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export async function fetchChats(search?: string): Promise<ChatResponse[]> {
  const params = new URLSearchParams();
  const q = search?.trim();
  if (q) params.set("q", q);
  const qs = params.toString();
  const res = await authFetch(apiUrl(`/api/chats${qs ? `?${qs}` : ""}`));
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

export async function fetchChatMessages(chatId: number): Promise<ApiMessage[]> {
  const res = await authFetch(apiUrl(`/api/chats/${chatId}/messages`));
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  return res.json();
}

interface StreamResult {
  content: string;
  metadata?: Record<string, unknown>;
}

export interface StreamEvent {
  type: "thinking" | "tool" | "agent" | "subagent" | "status" | "model" | "memory" | "task" | "ui";
  content?: string;
  name?: string;
  status?: string;
  agent_id?: string;
  task_id?: string;
  parent_id?: string;
  kind?: string;
  title?: string;
  short_title?: string;
  parallel_group?: string;
  depth?: number;
  source?: string;
  mcp_server?: string;
  tool_name?: string;
  block?: UiBlock;
}

export interface SSEStreamOptions {
  sessionId?: string;
  onEnvelope?: (envelope: AiEventEnvelope) => void;
  signal?: AbortSignal;
}

async function consumeSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onChunk?: (text: string) => void,
  onContext?: (context: ChatContextUsage) => void,
  onEvent?: (event: StreamEvent) => void,
  streamOptions?: SSEStreamOptions
): Promise<StreamResult> {
  const decoder = new TextDecoder();
  let buffer = "";
  let fullContent = "";
  let metadata: Record<string, unknown> | undefined;
  const uiBlocks: UiBlock[] = [];

  let currentTurnId = "";

  while (true) {
    if (streamOptions?.signal?.aborted) {
      reader.cancel().catch(() => undefined);
      break;
    }
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
        const parsed = JSON.parse(payload) as Record<string, unknown> & {
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
          source?: string;
          mcp_server?: string;
          tool_name?: string;
          block?: UiBlock;
          task_id?: string;
          parent_id?: string;
          kind?: string;
          title?: string;
          short_title?: string;
          parallel_group?: string;
          depth?: number;
        };

        // Final persisted assistant row — not a streaming chunk.
        if (parsed.id != null && parsed.role === "assistant") {
          if (typeof parsed.content === "string") {
            fullContent = parsed.content;
          }
          metadata = {
            ...metadata,
            ...parsed.metadata,
            ui_blocks:
              (parsed.metadata?.ui_blocks as UiBlock[] | undefined) ??
              (uiBlocks.length ? uiBlocks : undefined),
          };
          continue;
        }

        const sessionId = streamOptions?.sessionId ?? "0";
        const envelope = parseEnvelope(parsed, sessionId, currentTurnId || undefined);
        if (envelope) {
          if (envelope.turn_id) currentTurnId = envelope.turn_id;
          streamOptions?.onEnvelope?.(envelope);
          const streamEv = envelopeToStreamEvent(envelope);
          if (streamEv) onEvent?.(streamEv);
          if (envelope.type === "message.chunk") {
            const chunk = String(envelope.payload.content ?? parsed.content ?? "");
            if (chunk) {
              fullContent += chunk;
              onChunk?.(chunk);
            }
            eventBus.publishImmediate(envelope);
            continue;
          }
          eventBus.publish(envelope);
          if (envelope.type === "context.usage") {
            const ratio =
              envelope.payload.usage_ratio != null
                ? Number(envelope.payload.usage_ratio)
                : Math.min(1, Math.max(0, Number(envelope.payload.usage_percent ?? 0) / 100));
            const ctx: ChatContextUsage = {
              usage_ratio: ratio,
              used_tokens: Number(envelope.payload.used_tokens ?? 0),
              max_tokens: Number(envelope.payload.max_tokens ?? 128_000),
              usage_percent: Number(envelope.payload.usage_percent ?? Math.round(ratio * 100)),
              breakdown: (envelope.payload.breakdown as ChatContextUsage["breakdown"]) ?? {
                messages: 0,
                draft: 0,
                memory_recall: 0,
                system_overhead: 0,
              },
              message_count: Number(envelope.payload.message_count ?? 0),
              model_id: envelope.payload.model_id as string | undefined,
            };
            metadata = { ...metadata, context_usage: ctx };
            onContext?.(ctx);
            continue;
          }
          if (envelope.type === "stream.done") continue;
          continue;
        }

        if (
          parsed.type === "context" &&
          (parsed.usage_ratio != null || parsed.usage_percent != null)
        ) {
          const ratio =
            parsed.usage_ratio != null
              ? parsed.usage_ratio
              : Math.min(1, Math.max(0, (parsed.usage_percent ?? 0) / 100));
          const ctx: ChatContextUsage = {
            usage_ratio: ratio,
            used_tokens: parsed.used_tokens ?? 0,
            max_tokens: parsed.max_tokens ?? 128_000,
            usage_percent: parsed.usage_percent ?? Math.round(ratio * 100),
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

        if (parsed.type === "content" && typeof parsed.content === "string") {
          // Skip if already handled via envelope wrapper (has nested envelope field)
          if (parsed.envelope) continue;
          if (parsed.content) {
            fullContent += parsed.content;
            onChunk?.(parsed.content);
          }
          continue;
        }

        if (parsed.type === "ui" && parsed.block) {
          const block = coerceUiBlock(parsed.block);
          if (block) {
            const merged = mergeUiBlocks(uiBlocks, [block]);
            uiBlocks.length = 0;
            uiBlocks.push(...merged);
            onEvent?.({
              type: "ui",
              block,
              source: parsed.source,
              tool_name: parsed.tool_name,
            });
          }
          continue;
        }

        if (parsed.type === "tool") {
          onEvent?.({
            type: "tool",
            name: parsed.name,
            status: parsed.status,
            agent_id: parsed.agent_id,
            source: parsed.source,
            mcp_server: parsed.mcp_server,
          });
          continue;
        }

        if (parsed.type === "memory") {
          onEvent?.({ type: "memory", name: parsed.name, status: parsed.status });
          continue;
        }

        if (parsed.type === "task") {
          onEvent?.({
            type: "task",
            task_id: parsed.task_id,
            parent_id: parsed.parent_id,
            kind: parsed.kind,
            name: parsed.name,
            title: parsed.title,
            short_title: parsed.short_title,
            status: parsed.status,
            agent_id: parsed.agent_id,
            parallel_group: parsed.parallel_group,
            depth: parsed.depth,
          });
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

        fullContent += parsed.content;
        onChunk?.(parsed.content);
      } catch {
        // Ignore malformed SSE JSON lines.
      }
    }
  }

  if (uiBlocks.length) {
    metadata = { ...metadata, ui_blocks: uiBlocks };
  }

  return { content: fullContent, metadata };
}

export interface VoiceAttachmentPayload {
  data: string;
  mime_type: string;
  duration_ms?: number;
}

async function blobToBase64(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]!);
  }
  return btoa(binary);
}

export async function voiceBlobToPayload(
  blob: Blob,
  mimeType: string,
  durationMs?: number
): Promise<VoiceAttachmentPayload> {
  return {
    data: await blobToBase64(blob),
    mime_type: mimeType,
    ...(durationMs != null ? { duration_ms: durationMs } : {}),
  };
}

export async function sendMessage(
  chatId: number,
  content: string,
  onChunk?: (chunk: string) => void,
  modelId?: string,
  onContext?: (context: ChatContextUsage) => void,
  metadata?: Record<string, unknown>,
  onEvent?: (event: StreamEvent) => void,
  voice?: VoiceAttachmentPayload,
  streamOptions?: SSEStreamOptions
): Promise<{ content: string; metadata?: Record<string, unknown> }> {
  const mergedMetadata = { ...(metadata ?? {}) };
  if (voice) {
    mergedMetadata.voice = voice;
  }

  const res = await authFetch(apiUrl(`/api/chats/${chatId}/messages`), {
    method: "POST",
    body: JSON.stringify({
      content,
      model_id: modelId,
      metadata: mergedMetadata,
    }),
    signal: streamOptions?.signal,
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("text/event-stream") || contentType.includes("application/x-ndjson")) {
    const reader = res.body?.getReader();
    if (!reader) throw new Error("No response body");
    return consumeSSEStream(reader, onChunk, onContext, onEvent, {
      sessionId: String(chatId),
      ...streamOptions,
    });
  }

  const data = await res.json();
  const text = data.response ?? data.content ?? "";
  onChunk?.(text);
  return { content: text, metadata: data.metadata };
}

export { clearAuthSession };
