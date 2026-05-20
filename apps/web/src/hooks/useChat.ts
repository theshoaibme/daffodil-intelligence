import { useState, useCallback } from "react";
import { 
  createChat, 
  sendMessage 
} from "../lib/api";

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
  const [chatId, setChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingContent, setCurrentStreamingContent] = useState("");
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [error, setError] = useState<string | null>(null);

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