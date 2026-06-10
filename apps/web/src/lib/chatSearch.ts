import type { ChatHistoryEntry } from "./chatHistoryStorage";

/** Normalize text for consistent, case-insensitive matching. */
export function normalizeSearchText(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function searchableBlob(entry: ChatHistoryEntry): string {
  const parts = [entry.title];
  for (const message of entry.messages) {
    if (message.content?.trim()) parts.push(message.content);
    const meta = message.metadata;
    if (meta && typeof meta === "object") {
      const thinking = meta.thinking_text;
      if (typeof thinking === "string" && thinking.trim()) parts.push(thinking);
    }
  }
  return normalizeSearchText(parts.join("\n"));
}

/** True when every query token appears somewhere in the chat title or messages. */
export function chatHistoryMatchesQuery(entry: ChatHistoryEntry, query: string): boolean {
  const normalized = normalizeSearchText(query);
  if (!normalized) return true;

  const haystack = searchableBlob(entry);
  const tokens = normalized.split(/\s+/).filter(Boolean);
  return tokens.every((token) => haystack.includes(token));
}

export function filterChatHistories(
  entries: ChatHistoryEntry[],
  query: string
): ChatHistoryEntry[] {
  if (!normalizeSearchText(query)) return entries;
  return entries.filter((entry) => chatHistoryMatchesQuery(entry, query));
}
