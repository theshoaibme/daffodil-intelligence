import type { ChatMessage } from "../hooks/useChat";
import { loadChatSession } from "./chatStorage";

const HISTORY_KEY = "di-dashboard-chat-history";
const ACTIVE_KEY = "di-dashboard-active-chat-id";

export interface ChatHistoryEntry {
  id: string;
  title: string;
  updatedAt: string;
  chatId: number | null;
  messages: Array<Omit<ChatMessage, "timestamp"> & { timestamp: string }>;
}

const SEED_HISTORY_IDS = new Set(["seed-thesis-hub", "seed-uniproject-hub"]);

function stripSeedHistory(entries: ChatHistoryEntry[]): ChatHistoryEntry[] {
  return entries.filter((entry) => !SEED_HISTORY_IDS.has(entry.id));
}

export function generateChatSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

function serializeMessages(messages: ChatMessage[]) {
  return messages.map((message) => ({
    ...message,
    isStreaming: false,
    timestamp: message.timestamp.toISOString(),
  }));
}

function deserializeMessages(
  messages: ChatHistoryEntry["messages"]
): ChatMessage[] {
  return messages.map((message) => ({
    ...message,
    isStreaming: false,
    timestamp: new Date(message.timestamp),
  }));
}

function deriveTitle(messages: ChatMessage[]): string {
  const firstUser = messages.find((message) => message.role === "user");
  if (!firstUser?.content.trim()) return "New chat";
  const text = firstUser.content.trim();
  return text.length > 42 ? `${text.slice(0, 42)}…` : text;
}

function migrateLegacySession(history: ChatHistoryEntry[]): ChatHistoryEntry[] {
  const legacy = loadChatSession();
  if (!legacy?.messages.length) return history;

  const existing = history.find((entry) => entry.chatId === legacy.chatId);
  if (existing) return history;

  return [
    {
      id: generateChatSessionId(),
      title: deriveTitle(legacy.messages),
      updatedAt: new Date().toISOString(),
      chatId: legacy.chatId,
      messages: serializeMessages(legacy.messages),
    },
    ...history,
  ];
}

export function loadChatHistory(): ChatHistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? stripSeedHistory(JSON.parse(raw) as ChatHistoryEntry[]) : [];
    const withLegacy = migrateLegacySession(parsed);
    if (!raw || withLegacy.length !== parsed.length) {
      saveChatHistory(withLegacy);
    }
    return withLegacy;
  } catch {
    return [];
  }
}

export function saveChatHistory(entries: ChatHistoryEntry[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
  } catch {
    // Ignore quota / private mode errors.
  }
}

export function getActiveHistoryId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_KEY);
  } catch {
    return null;
  }
}

export function setActiveHistoryId(id: string | null) {
  try {
    if (id) localStorage.setItem(ACTIVE_KEY, id);
    else localStorage.removeItem(ACTIVE_KEY);
  } catch {
    // Ignore storage errors.
  }
}

export function formatHistoryDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function createHistorySession(title = "New chat"): ChatHistoryEntry {
  const entries = pruneEmptyGenericSessions(loadChatHistory());
  const entry: ChatHistoryEntry = {
    id: generateChatSessionId(),
    title,
    updatedAt: new Date().toISOString(),
    chatId: null,
    messages: [],
  };
  const next = [entry, ...entries];
  saveChatHistory(next);
  setActiveHistoryId(entry.id);
  return entry;
}

/** Remove stale empty "New agent" stubs before creating a fresh session. */
function pruneEmptyGenericSessions(entries: ChatHistoryEntry[]): ChatHistoryEntry[] {
  return entries.filter(
    (entry) =>
      !(
        entry.messages.length === 0 &&
        entry.chatId == null &&
        isGenericTitle(entry.title)
      )
  );
}

/** Link a server chat id to a sidebar session before messages are persisted. */
export function bindChatIdToSession(sessionId: string, chatId: number): ChatHistoryEntry[] {
  const entries = loadChatHistory();
  const index = entries.findIndex((entry) => entry.id === sessionId);
  if (index < 0) return entries;
  if (entries[index].chatId === chatId) return entries;

  const next = [...entries];
  next[index] = {
    ...next[index],
    chatId,
    updatedAt: new Date().toISOString(),
  };
  saveChatHistory(next);
  return next;
}

export function upsertHistoryEntry(
  activeId: string | null,
  chatId: number | null,
  messages: ChatMessage[]
): { entries: ChatHistoryEntry[]; activeId: string | null } {
  const entries = loadChatHistory();
  if (!messages.length) return { entries, activeId };

  const payload = {
    title: deriveTitle(messages),
    updatedAt: new Date().toISOString(),
    chatId,
    messages: serializeMessages(messages),
  };

  if (activeId) {
    const index = entries.findIndex((entry) => entry.id === activeId);
    if (index >= 0) {
      entries[index] = { ...entries[index], ...payload };
      saveChatHistory(entries);
      return { entries, activeId };
    }
    return { entries, activeId };
  }

  return { entries, activeId };
}

export function deleteHistoryEntry(id: string): ChatHistoryEntry[] {
  const entries = loadChatHistory().filter((entry) => entry.id !== id);
  saveChatHistory(entries);
  if (getActiveHistoryId() === id) setActiveHistoryId(null);
  return entries;
}

function isGenericTitle(title: string): boolean {
  const normalized = title.trim().toLowerCase();
  return !normalized || normalized === "new chat" || normalized === "new agent";
}

export interface ServerChatSummary {
  id: number;
  title: string;
  created_at: string;
}

/** Merge API chat rows into local history (by chatId) without dropping local messages. */
export function mergeServerChats(serverChats: ServerChatSummary[]): ChatHistoryEntry[] {
  const entries = loadChatHistory();
  const byChatId = new Map<number, number>();
  entries.forEach((entry, index) => {
    if (entry.chatId != null) byChatId.set(entry.chatId, index);
  });

  let changed = false;
  const next = [...entries];

  for (const chat of serverChats) {
    const idx = byChatId.get(chat.id);
    if (idx !== undefined) {
      const existing = next[idx];
      const serverTitle = chat.title?.trim() || "Chat";
      if (isGenericTitle(existing.title) && !isGenericTitle(serverTitle)) {
        next[idx] = { ...existing, title: serverTitle, updatedAt: chat.created_at };
        changed = true;
      }
      continue;
    }

    next.push({
      id: generateChatSessionId(),
      title: chat.title?.trim() || "Chat",
      updatedAt: chat.created_at,
      chatId: chat.id,
      messages: [],
    });
    changed = true;
  }

  next.sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );

  if (changed) saveChatHistory(next);
  return next;
}

export function apiMessagesToStoredMessages(
  messages: Array<{
    id: number;
    role: string;
    content: string;
    metadata?: Record<string, unknown>;
    created_at: string;
  }>
): ChatHistoryEntry["messages"] {
  return messages.map((message) => ({
    id: `msg-${message.id}`,
    role: message.role as "user" | "assistant",
    content: message.content,
    timestamp: message.created_at,
    metadata: message.metadata,
  }));
}

export function updateHistoryMessages(
  id: string,
  messages: ChatHistoryEntry["messages"]
): ChatHistoryEntry[] {
  const entries = loadChatHistory();
  const index = entries.findIndex((entry) => entry.id === id);
  if (index < 0) return entries;

  const next = [...entries];
  next[index] = {
    ...next[index],
    messages,
    updatedAt: new Date().toISOString(),
    title: messages.length
      ? deriveTitle(
          messages.map((m) => ({
            ...m,
            isStreaming: false,
            timestamp: new Date(m.timestamp),
          }))
        )
      : next[index].title,
  };
  saveChatHistory(next);
  return next;
}

export function getHistoryEntry(id: string): {
  chatId: number | null;
  messages: ChatMessage[];
} | null {
  const entry = loadChatHistory().find((item) => item.id === id);
  if (!entry) return null;
  return {
    chatId: entry.chatId,
    messages: deserializeMessages(entry.messages),
  };
}
