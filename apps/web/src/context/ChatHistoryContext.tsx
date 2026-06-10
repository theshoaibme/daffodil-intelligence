import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ROUTES } from "@lib";
import { fetchChatMessages, fetchChats } from "@lib";
import {
  apiMessagesToStoredMessages,
  createHistorySession,
  deleteHistoryEntry,
  getActiveHistoryId,
  loadChatHistory,
  mergeServerChats,
  setActiveHistoryId,
  updateHistoryMessages,
  upsertHistoryEntry,
  type ChatHistoryEntry,
} from "@lib";
import type { ChatMessage } from "@hooks";
import { useAuth } from "./AuthContext";

export interface ChatSessionState {
  sessionId: string;
  chatId: number | null;
  messages: ChatMessage[];
}

interface ChatHistoryContextValue {
  histories: ChatHistoryEntry[];
  activeHistoryId: string | null;
  selectHistory: (id: string) => Promise<ChatSessionState>;
  startNewChat: () => ChatSessionState;
  deleteHistory: (id: string) => void;
  shareHistory: (id: string) => Promise<void>;
  syncActiveSession: (chatId: number | null, messages: ChatMessage[]) => void;
  refreshHistories: () => void;
  syncFromApi: (search?: string) => Promise<void>;
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
  const { isAuthenticated } = useAuth();
  const [histories, setHistories] = useState<ChatHistoryEntry[]>(() => loadChatHistory());
  const [activeHistoryId, setActiveId] = useState<string | null>(() => getActiveHistoryId());
  const syncRequestRef = useRef(0);

  const refreshHistories = useCallback(() => {
    setHistories(loadChatHistory());
    setActiveId(getActiveHistoryId());
  }, []);

  const syncFromApi = useCallback(async (search?: string) => {
    if (!isAuthenticated) return;
    const requestId = ++syncRequestRef.current;
    try {
      const remote = await fetchChats(search);
      if (requestId !== syncRequestRef.current) return;
      setHistories(mergeServerChats(remote));
    } catch {
      // Offline or auth errors — keep local history.
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    void syncFromApi();
  }, [isAuthenticated, syncFromApi]);

  const hydrateMessages = useCallback(async (entry: ChatHistoryEntry): Promise<ChatSessionState> => {
    if (!entry.chatId || entry.messages.length > 0) {
      return toSessionState(entry);
    }

    try {
      const remoteMessages = await fetchChatMessages(entry.chatId);
      const stored = apiMessagesToStoredMessages(remoteMessages);
      const next = updateHistoryMessages(entry.id, stored);
      setHistories(next);
      const updated = next.find((item) => item.id === entry.id) ?? entry;
      return toSessionState(updated);
    } catch {
      return toSessionState(entry);
    }
  }, []);

  const selectHistory = useCallback(async (id: string): Promise<ChatSessionState> => {
    const entry = loadChatHistory().find((item) => item.id === id);
    setActiveHistoryId(id);
    setActiveId(id);
    if (!entry) {
      return { sessionId: id, chatId: null, messages: [] };
    }
    return hydrateMessages(entry);
  }, [hydrateMessages]);

  const startNewChat = useCallback((): ChatSessionState => {
    const entry = createHistorySession("New agent");
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
      syncFromApi,
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
      syncFromApi,
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
