import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ROUTES } from "../lib/routes";
import {
  createHistorySession,
  deleteHistoryEntry,
  getActiveHistoryId,
  loadChatHistory,
  setActiveHistoryId,
  upsertHistoryEntry,
  type ChatHistoryEntry,
} from "../lib/chatHistoryStorage";
import type { ChatMessage } from "../hooks/useChat";

export interface ChatSessionState {
  sessionId: string;
  chatId: number | null;
  messages: ChatMessage[];
}

interface ChatHistoryContextValue {
  histories: ChatHistoryEntry[];
  activeHistoryId: string | null;
  selectHistory: (id: string) => ChatSessionState;
  startNewChat: () => ChatSessionState;
  deleteHistory: (id: string) => void;
  shareHistory: (id: string) => Promise<void>;
  syncActiveSession: (chatId: number | null, messages: ChatMessage[]) => void;
  refreshHistories: () => void;
}

const ChatHistoryContext = createContext<ChatHistoryContextValue | null>(null);

function toSessionState(entry: ChatHistoryEntry): ChatSessionState {
  return {
    sessionId: entry.id,
    chatId: entry.chatId,
    messages: entry.messages.map((message) => ({
      ...message,
      isStreaming: false,
      timestamp: new Date(message.timestamp),
    })),
  };
}

export function ChatHistoryProvider({ children }: { children: ReactNode }) {
  const [histories, setHistories] = useState<ChatHistoryEntry[]>(() => loadChatHistory());
  const [activeHistoryId, setActiveId] = useState<string | null>(() => getActiveHistoryId());

  const refreshHistories = useCallback(() => {
    setHistories(loadChatHistory());
    setActiveId(getActiveHistoryId());
  }, []);

  const selectHistory = useCallback((id: string): ChatSessionState => {
    const entry = loadChatHistory().find((item) => item.id === id);
    setActiveHistoryId(id);
    setActiveId(id);
    if (!entry) {
      return { sessionId: id, chatId: null, messages: [] };
    }
    return toSessionState(entry);
  }, []);

  const startNewChat = useCallback((): ChatSessionState => {
    const entry = createHistorySession("New chat");
    setHistories(loadChatHistory());
    setActiveId(entry.id);
    return toSessionState(entry);
  }, []);

  const deleteHistory = useCallback((id: string) => {
    const next = deleteHistoryEntry(id);
    setHistories(next);
    setActiveId(getActiveHistoryId());
  }, []);

  const shareHistory = useCallback(async (id: string) => {
    const entry = loadChatHistory().find((item) => item.id === id);
    if (!entry) return;

    const url = `${window.location.origin}${ROUTES.home}?chat=${id}`;
    const shareData = {
      title: entry.title,
      text: `Chat: ${entry.title}`,
      url,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
        return;
      } catch {
        // Fall through to clipboard copy.
      }
    }

    await navigator.clipboard.writeText(url);
  }, []);

  const syncActiveSession = useCallback(
    (chatId: number | null, messages: ChatMessage[]) => {
      const { entries, activeId } = upsertHistoryEntry(activeHistoryId, chatId, messages);
      setHistories(entries);
      if (activeId) {
        setActiveHistoryId(activeId);
        setActiveId(activeId);
      }
    },
    [activeHistoryId]
  );

  useEffect(() => {
    refreshHistories();
  }, [refreshHistories]);

  const value = useMemo(
    () => ({
      histories,
      activeHistoryId,
      selectHistory,
      startNewChat,
      deleteHistory,
      shareHistory,
      syncActiveSession,
      refreshHistories,
    }),
    [
      histories,
      activeHistoryId,
      selectHistory,
      startNewChat,
      deleteHistory,
      shareHistory,
      syncActiveSession,
      refreshHistories,
    ]
  );

  return (
    <ChatHistoryContext.Provider value={value}>{children}</ChatHistoryContext.Provider>
  );
}

export function useChatHistory() {
  const context = useContext(ChatHistoryContext);
  if (!context) {
    throw new Error("useChatHistory must be used within ChatHistoryProvider");
  }
  return context;
}
