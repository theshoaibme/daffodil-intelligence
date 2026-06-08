import { useState, useCallback, useEffect } from "react";
import { 
  createChat, 
  sendMessage 
} from "../lib/api";
import { clearChatSession, loadChatSession, saveChatSession } from "../lib/chatStorage";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  metadata?: {
    agent?: string;
    tools_used?: string[];
    sources?: string[];
  };
  isStreaming?: boolean;
}

export interface ThinkingStep {
  id: string;
  title: string;
  status: "pending" | "active" | "success";
}

export function useChat() {
  const [chatId, setChatId] = useState<number | null>(() => loadChatSession()?.chatId ?? null);
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadChatSession()?.messages ?? []);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingContent, setCurrentStreamingContent] = useState("");
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isStreaming) return;
    saveChatSession(chatId, messages);
  }, [chatId, messages, isStreaming]);

  const initializeChat = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const chat = await createChat("supervisor");
      setChatId(chat.id);
      return chat;
    } catch (err) {
      setError("Failed to initialize chat");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const send = useCallback(async (content: string) => {
    try {
      setError(null);
      setIsLoading(true);
      setIsStreaming(true);

      let currentChatId = chatId;
      
      if (!currentChatId) {
        const chat = await createChat("supervisor");
        currentChatId = chat.id;
        setChatId(chat.id);
      }

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, userMessage]);

      setThinkingSteps([]);

      const assistantMessageId = `assistant-${Date.now()}`;
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setCurrentStreamingContent("");

      let fullContent = "";

      const response = await sendMessage(currentChatId, content, (chunk) => {
        fullContent += chunk;
        setCurrentStreamingContent(fullContent);
        
        setMessages(prev => 
          prev.map(m => 
            m.id === assistantMessageId 
              ? { ...m, content: fullContent } 
              : m
          )
        );
      });

      setThinkingSteps(prev => 
        prev.map(s => ({ ...s, status: "success" }))
      );

      setMessages(prev => 
        prev.map(m => 
          m.id === assistantMessageId 
            ? { 
                ...m, 
                content: response.content,
                metadata: response.metadata,
                isStreaming: false,
              } 
            : m
        )
      );

      setIsStreaming(false);
      setCurrentStreamingContent("");
      
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      setIsStreaming(false);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  const clearChat = useCallback(() => {
    setChatId(null);
    setMessages([]);
    setThinkingSteps([]);
    setCurrentStreamingContent("");
    setError(null);
    clearChatSession();
  }, []);

  return {
    chatId,
    messages,
    isLoading,
    isStreaming,
    currentStreamingContent,
    thinkingSteps,
    error,
    send,
    clearChat,
    initializeChat,
  };
}