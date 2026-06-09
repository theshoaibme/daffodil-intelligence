import { useState, useCallback, useRef } from "react";
import {
  createChat,
  sendMessage,
} from "../lib/api";
import type { StreamEvent } from "../lib/api";
import type { ChatContextUsage } from "../lib/chatContext";

function humanizeName(name: string): string {
  return name
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

function normalizeStatus(status?: string): ThinkingStep["status"] {
  if (status === "success" || status === "done" || status === "completed") return "success";
  if (status === "active" || status === "running" || status === "start") return "active";
  return "active";
}

function upsertStep(
  steps: ThinkingStep[],
  id: string,
  title: string,
  status: ThinkingStep["status"]
): ThinkingStep[] {
  const existing = steps.find((s) => s.id === id);
  if (!existing) {
    return [...steps, { id, title, status }];
  }
  return steps.map((s) => (s.id === id ? { ...s, status } : s));
}

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

interface UseChatOptions {
  initialChatId?: number | null;
  initialMessages?: ChatMessage[];
}

export function useChat(options?: UseChatOptions) {
  const [chatId, setChatId] = useState<number | null>(options?.initialChatId ?? null);
  const [messages, setMessages] = useState<ChatMessage[]>(options?.initialMessages ?? []);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingContent, setCurrentStreamingContent] = useState("");
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [thinkingText, setThinkingText] = useState("");
  const [thinkingMs, setThinkingMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastContext, setLastContext] = useState<ChatContextUsage | null>(null);
  const sendGenerationRef = useRef(0);
  const thinkingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const thinkingStartRef = useRef<number | null>(null);

  const stopThinkingTimer = useCallback(() => {
    if (thinkingTimerRef.current) {
      clearInterval(thinkingTimerRef.current);
      thinkingTimerRef.current = null;
    }
  }, []);

  const isSendStale = useCallback(
    (generation: number) => generation !== sendGenerationRef.current,
    []
  );

  const loadSession = useCallback((nextChatId: number | null, nextMessages: ChatMessage[]) => {
    sendGenerationRef.current += 1;
    stopThinkingTimer();
    thinkingStartRef.current = null;
    setChatId(nextChatId);
    setMessages(nextMessages);
    setThinkingSteps([]);
    setThinkingText("");
    setThinkingMs(null);
    setCurrentStreamingContent("");
    setError(null);
    setIsLoading(false);
    setIsStreaming(false);
    setLastContext(null);
  }, [stopThinkingTimer]);

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

  const send = useCallback(async (
    content: string,
    modelId?: string,
    metadata?: Record<string, unknown>
  ) => {
    const generation = sendGenerationRef.current;

    try {
      setError(null);
      setIsLoading(true);
      setIsStreaming(true);

      let currentChatId = chatId;
      
      if (!currentChatId) {
        const chat = await createChat("supervisor");
        if (isSendStale(generation)) return;
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
      setThinkingText("");
      setThinkingMs(0);
      thinkingStartRef.current = Date.now();
      stopThinkingTimer();
      thinkingTimerRef.current = setInterval(() => {
        if (thinkingStartRef.current != null && !isSendStale(generation)) {
          setThinkingMs(Date.now() - thinkingStartRef.current);
        }
      }, 100);

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

      const response = await sendMessage(
        currentChatId,
        content,
        (chunk) => {
          if (isSendStale(generation)) return;
          if (thinkingTimerRef.current) {
            stopThinkingTimer();
            if (thinkingStartRef.current != null) {
              setThinkingMs(Date.now() - thinkingStartRef.current);
            }
            setThinkingSteps((prev) =>
              prev.map((s) => (s.status === "active" ? { ...s, status: "success" } : s))
            );
          }
          fullContent += chunk;
          setCurrentStreamingContent(fullContent);

          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId ? { ...m, content: fullContent } : m
            )
          );
        },
        modelId,
        (ctx) => {
          if (!isSendStale(generation)) setLastContext(ctx);
        },
        metadata,
        (event: StreamEvent) => {
          if (isSendStale(generation)) return;
          if (event.type === "thinking" && event.content) {
            setThinkingText((prev) => prev + event.content);
          } else if (event.type === "tool" && event.name) {
            setThinkingSteps((prev) =>
              upsertStep(
                prev,
                `tool:${event.name}`,
                `Using ${humanizeName(event.name!)}`,
                normalizeStatus(event.status)
              )
            );
          } else if ((event.type === "agent" || event.type === "subagent") && event.name) {
            const label = event.type === "subagent" ? "Delegating to" : "Agent";
            setThinkingSteps((prev) =>
              upsertStep(
                prev,
                `${event.type}:${event.agent_id ?? event.name}`,
                `${label} ${humanizeName(event.name!)}`,
                normalizeStatus(event.status)
              )
            );
          }
        }
      );

      if (isSendStale(generation)) return;

      if (thinkingTimerRef.current) {
        stopThinkingTimer();
        if (thinkingStartRef.current != null) {
          setThinkingMs(Date.now() - thinkingStartRef.current);
        }
      }

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
      stopThinkingTimer();
      if (isSendStale(generation)) return;
      setError(err instanceof Error ? err.message : "Failed to send message");
      setIsStreaming(false);
      throw err;
    } finally {
      if (!isSendStale(generation)) {
        setIsLoading(false);
      }
    }
  }, [chatId, isSendStale, stopThinkingTimer]);

  const clearChat = useCallback(() => {
    loadSession(null, []);
  }, [loadSession]);

  return {
    chatId,
    messages,
    isLoading,
    isStreaming,
    currentStreamingContent,
    thinkingSteps,
    thinkingText,
    thinkingMs,
    error,
    lastContext,
    send,
    clearChat,
    loadSession,
    initializeChat,
  };
}