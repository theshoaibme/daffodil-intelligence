import { useState, useCallback, useRef } from "react";
import {
  createChat,
  sendMessage,
} from "../lib/api";
import type { StreamEvent } from "../lib/api";
import {
  activeAgentsFromTasks,
  activeToolsFromTasks,
  agentForTool,
  memoryActiveFromTasks,
  reduceAgentTasks,
  tasksToPanelItems,
  type AgentTaskNode,
} from "../lib/agentTasks";
import { emitFlow, getFlow, resetFlow } from "../lib/flowBus";
import type { ChatContextUsage } from "../lib/chatContext";

function syncFlowFromTasks(tasks: AgentTaskNode[], inputId: string | null) {
  const activeAgents = activeAgentsFromTasks(tasks);
  const withoutMain = activeAgents.filter((id) => id !== "main");
  emitFlow({
    modelActive: tasks.some((t) => t.status === "active"),
    activeAgentIds: withoutMain.length > 0 ? withoutMain : activeAgents,
    activeTools: activeToolsFromTasks(tasks),
    memoryActive: memoryActiveFromTasks(tasks),
    activeInputId: inputId,
  });
}

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
  const [agentTasks, setAgentTasks] = useState<AgentTaskNode[]>([]);
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
    resetFlow();
    thinkingStartRef.current = null;
    setChatId(nextChatId);
    setMessages(nextMessages);
    setThinkingSteps([]);
    setAgentTasks([]);
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
      setAgentTasks([]);
      setThinkingText("");
      setThinkingMs(0);
      resetFlow();
      const channel = (metadata?.channel as string) || "chat";
      const inputId = channel === "telegram" ? "input-telegram" : "input-chat";
      emitFlow({
        activeInputId: inputId,
        activeAgentIds: [],
        activeTools: [],
        memoryActive: false,
        modelActive: false,
      });
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
          const inputId = getFlow().activeInputId ?? "input-chat";

          if (event.type === "thinking" && event.content) {
            setThinkingText((prev) => prev + event.content);
            return;
          }

          if (
            event.type === "task" ||
            event.type === "tool" ||
            event.type === "agent" ||
            event.type === "subagent" ||
            event.type === "memory" ||
            event.type === "model" ||
            event.type === "status"
          ) {
            setAgentTasks((prev) => {
              const next = reduceAgentTasks(prev, event);
              syncFlowFromTasks(next, inputId);
              const panel = tasksToPanelItems(next);
              setThinkingSteps(
                panel.map((p) => ({
                  id: p.id,
                  title: p.text,
                  status: p.active ? "active" : "success",
                }))
              );
              return next;
            });
          }

          if (event.type === "tool" && event.name && normalizeStatus(event.status) === "active") {
            const extra = agentForTool(event.name, event.agent_id).filter((id) => id !== "main");
            const flow = getFlow();
            emitFlow({
              modelActive: true,
              activeAgentIds: Array.from(new Set([...flow.activeAgentIds, ...extra])),
              activeTools: Array.from(new Set([...flow.activeTools, event.name!])),
              activeInputId: inputId,
            });
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
      resetFlow();

      return response;
    } catch (err) {
      stopThinkingTimer();
      resetFlow();
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

  const truncateFromMessage = useCallback(
    (messageId: string) => {
      sendGenerationRef.current += 1;
      stopThinkingTimer();
      resetFlow();
      thinkingStartRef.current = null;
      setThinkingSteps([]);
      setThinkingText("");
      setThinkingMs(null);
      setCurrentStreamingContent("");
      setError(null);
      setIsLoading(false);
      setIsStreaming(false);
      setMessages((prev) => {
        const index = prev.findIndex((message) => message.id === messageId);
        if (index < 0) return prev;
        return prev.slice(0, index);
      });
    },
    [stopThinkingTimer]
  );

  return {
    chatId,
    messages,
    isLoading,
    isStreaming,
    currentStreamingContent,
    thinkingSteps,
    agentTasks,
    thinkingText,
    thinkingMs,
    error,
    lastContext,
    send,
    clearChat,
    loadSession,
    initializeChat,
    truncateFromMessage,
  };
}