import type { ChatMessage } from "../hooks/useChat";

const CHAT_SESSION_KEY = "di-dashboard-chat-session";

interface StoredChatSession {
  chatId: number | null;
  messages: Array<
    Omit<ChatMessage, "timestamp"> & {
      timestamp: string;
    }
  >;
}

export function loadChatSession(): {
  chatId: number | null;
  messages: ChatMessage[];
} | null {
  try {
    const raw = localStorage.getItem(CHAT_SESSION_KEY);
    if (!raw) return null;

    const data = JSON.parse(raw) as StoredChatSession;
    if (!data.messages?.length) return null;

    return {
      chatId: data.chatId ?? null,
      messages: data.messages.map((message) => ({
        ...message,
        isStreaming: false,
        timestamp: new Date(message.timestamp),
      })),
    };
  } catch {
    return null;
  }
}

export function saveChatSession(chatId: number | null, messages: ChatMessage[]) {
  if (!messages.length) {
    localStorage.removeItem(CHAT_SESSION_KEY);
    return;
  }

  const payload: StoredChatSession = {
    chatId,
    messages: messages.map((message) => ({
      ...message,
      isStreaming: false,
      timestamp: message.timestamp.toISOString(),
    })),
  };

  try {
    localStorage.setItem(CHAT_SESSION_KEY, JSON.stringify(payload));
  } catch {
    // Ignore quota / private mode errors.
  }
}

export function clearChatSession() {
  localStorage.removeItem(CHAT_SESSION_KEY);
}
