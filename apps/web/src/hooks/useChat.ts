import { useState, useCallback, useRef, useEffect } from "react";
import {
  createChat,
  sendMessage,
} from "../lib/api";
import type { StreamEvent } from "../lib/api";
import {
  activeAgentsFromTasks,
  activeToolsFromTasks,
  memoryActiveFromTasks,
  reduceAgentTasks,
  tasksToPanelItems,
  type AgentTaskNode,
} from "../lib/agentTasks";
import { emitFlow, getFlow, resetFlow, setFlow } from "../lib/flowBus";
import type { ChatContextUsage } from "../lib/chatContext";
import { coerceUiBlock, mergeUiBlocks } from "../lib/uiBlocks/coerce";
import type { UiBlock } from "../lib/uiBlocks/types";

function syncFlowFromTasks(tasks: AgentTaskNode[], inputId: string | null) {
  const activeAgents = activeAgentsFromTasks(tasks);
  const withoutMain = activeAgents.filter((id) => id !== "main");
  const modelTask = tasks.find((t) => t.kind === "model");
  const modelLabel = modelTask?.title?.replace(/^Model:\s*/i, "").trim();
  setFlow({
    modelActive: tasks.some((t) => t.status === "active"),
    activeAgentIds: withoutMain.length > 0 ? withoutMain : activeAgents,
    activeTools: activeToolsFromTasks(tasks),
    memoryActive: memoryActiveFromTasks(tasks),
    activeInputId: inputId,
    activeModelId: modelLabel || undefined,
  });
}

function finalizeAgentTasks(tasks: AgentTaskNode[]): AgentTaskNode[] {
  return tasks.map((t) =>
    t.status === "active" ? { ...t, status: "success" as const } : t
  );
}

function pruneLegacyTasks(tasks: AgentTaskNode[]): AgentTaskNode[] {
  if (!tasks.some((t) => t.id.startsWith("task-") || t.id.startsWith("root-"))) {
    return tasks;
  }
  return tasks.filter((t) => !t.id.startsWith("agent:") && !t.id.startsWith("tool:"));
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
    ui_blocks?: UiBlock[];
    [key: string]: unknown;
  };
  isStreaming?: boolean;
}

function withCoercedUiBlocks(messages: ChatMessage[]): ChatMessage[] {
  return messages.map((m) => {
    const raw = m.metadata?.ui_blocks;
    if (!Array.isArray(raw) || raw.length === 0) return m;
    return {
      ...m,
      metadata: { ...m.metadata, ui_blocks: mergeUiBlocks(raw) },
    };
  });
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

  useEffect(() => {
    const panel = tasksToPanelItems(agentTasks);
    setThinkingSteps(
      panel.map((p) => ({
        id: p.id,
        title: p.text,
        status: p.active ? ("active" as const) : ("success" as const),
      }))
    );
  }, [agentTasks]);

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
    setMessages(withCoercedUiBlocks(nextMessages));
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
      setLastContext(null);
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

          if (event.type === "ui" && event.block) {
            const block = coerceUiBlock(event.block);
            if (!block) return;
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantMessageId) return m;
                const existing = (m.metadata?.ui_blocks as UiBlock[] | undefined) ?? [];
                return {
                  ...m,
                  metadata: {
                    ...m.metadata,
                    ui_blocks: mergeUiBlocks(existing, [block]),
                  },
                };
              })
            );
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
              const reduced = reduceAgentTasks(prev, event);
              const next = pruneLegacyTasks(reduced);
              syncFlowFromTasks(next, inputId);
              return next;
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

      setAgentTasks((prev) => finalizeAgentTasks(prev));

      setMessages(prev =>
        prev.map((m) => {
          if (m.id !== assistantMessageId) return m;
          const streamedBlocks = (m.metadata?.ui_blocks as UiBlock[] | undefined) ?? [];
          const finalBlocks = mergeUiBlocks(
            streamedBlocks,
            (response.metadata?.ui_blocks as UiBlock[] | undefined) ?? []
          );
          return {
            ...m,
            content: response.content,
            metadata: {
              ...m.metadata,
              ...response.metadata,
              ui_blocks: finalBlocks.length ? finalBlocks : undefined,
            },
            isStreaming: false,
          };
        })
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
      setAgentTasks([]);
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