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
  const entry: ChatHistoryEntry = {
    id: generateChatSessionId(),
    title,
    updatedAt: new Date().toISOString(),
    chatId: null,
    messages: [],
  };
  const entries = [entry, ...loadChatHistory()];
  saveChatHistory(entries);
  setActiveHistoryId(entry.id);
  return entry;
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
  }

  const id = generateChatSessionId();
  const next = [{ id, ...payload }, ...entries];
  saveChatHistory(next);
  setActiveHistoryId(id);
  return { entries: next, activeId: id };
}

export function deleteHistoryEntry(id: string): ChatHistoryEntry[] {
  const entries = loadChatHistory().filter((entry) => entry.id !== id);
  saveChatHistory(entries);
  if (getActiveHistoryId() === id) setActiveHistoryId(null);
  return entries;
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
