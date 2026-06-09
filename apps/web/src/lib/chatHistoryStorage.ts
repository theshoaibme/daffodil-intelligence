export interface ChatHistoryEntry {
  id: string;
  chatId: number | null;
  title: string;
  messages: any[];
  timestamp: string; // ISO String
  updatedAt: string; // ISO String
}

const HISTORY_KEY = "di-chat-history";
const ACTIVE_ID_KEY = "di-active-history-id";

export function loadChatHistory(): ChatHistoryEntry[] {
  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    const parsed = stored ? JSON.parse(stored) : [];
    if (Array.isArray(parsed)) {
      // Sort by timestamp descending
      return parsed.sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
    }
    return [];
  } catch {
    return [];
  }
}

export function getActiveHistoryId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_ID_KEY);
  } catch {
    return null;
  }
}

export function setActiveHistoryId(id: string | null): void {
  try {
    if (id) {
      localStorage.setItem(ACTIVE_ID_KEY, id);
    } else {
      localStorage.removeItem(ACTIVE_ID_KEY);
    }
  } catch {}
}

export function getHistoryEntry(id: string): ChatHistoryEntry | null {
  const history = loadChatHistory();
  return history.find((e) => e.id === id) || null;
}

export function createHistorySession(title = "New chat"): ChatHistoryEntry {
  const now = new Date().toISOString();
  const newEntry: ChatHistoryEntry = {
    id: `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    chatId: null,
    title,
    messages: [],
    timestamp: now,
    updatedAt: now,
  };

  const history = loadChatHistory();
  const updated = [newEntry, ...history];
  localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  setActiveHistoryId(newEntry.id);
  return newEntry;
}

export function deleteHistoryEntry(id: string): ChatHistoryEntry[] {
  const history = loadChatHistory();
  const updated = history.filter((e) => e.id !== id);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));

  const activeId = getActiveHistoryId();
  if (activeId === id) {
    const nextActiveId = updated.length > 0 ? updated[0].id : null;
    setActiveHistoryId(nextActiveId);
  }

  return updated;
}

export function upsertHistoryEntry(
  id: string | null,
  chatId: number | null,
  messages: any[]
): { entries: ChatHistoryEntry[]; activeId: string | null } {
  let activeId = id;

  if (!activeId) {
    const newSession = createHistorySession("New chat");
    activeId = newSession.id;
  }

  const entries = loadChatHistory();
  const index = entries.findIndex((e) => e.id === activeId);
  if (index !== -1) {
    const entry = entries[index];
    entry.chatId = chatId;
    entry.messages = messages;
    const now = new Date().toISOString();
    entry.timestamp = now;
    entry.updatedAt = now;

    if (entry.title === "New chat" && messages.length > 0) {
      const firstUserMsg = messages.find((m) => m.role === "user");
      if (firstUserMsg && firstUserMsg.content) {
        const text = firstUserMsg.content.trim();
        entry.title = text.slice(0, 30) + (text.length > 30 ? "..." : "");
      }
    }

    entries[index] = entry;
  }

  localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
  return { entries, activeId };
}

export function formatHistoryDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  
  const diffTime = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 1) {
    if (date.getDate() === now.getDate()) {
      return "Today";
    }
    return "Yesterday";
  }
  if (diffDays === 1) {
    return "Yesterday";
  }
  if (diffDays < 7) {
    return `${diffDays} days ago`;
  }
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
