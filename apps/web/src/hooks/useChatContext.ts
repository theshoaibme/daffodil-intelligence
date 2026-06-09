import { useEffect, useState } from "react";
import { fetchChatContextUsage } from "../lib/api";
import {
  estimateContextUsage,
  type ChatContextUsage,
} from "../lib/chatContext";
import type { ChatMessage } from "./useChat";

export function useChatContext(
  chatId: number | null,
  messages: ChatMessage[],
  draft = "",
  modelId?: string
) {
  const [context, setContext] = useState<ChatContextUsage>(() =>
    estimateContextUsage(messages, draft)
  );

  useEffect(() => {
    if (!chatId) {
      setContext(estimateContextUsage(messages, draft));
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const data = await fetchChatContextUsage(chatId, draft, modelId);
        if (!cancelled) setContext(data);
      } catch {
        if (!cancelled) setContext(estimateContextUsage(messages, draft));
      }
    }, draft ? 250 : 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [chatId, messages, draft, modelId]);

  return context;
}
