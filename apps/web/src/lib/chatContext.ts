import type { ChatMessage } from "@hooks";

export interface ContextUsageBreakdown {
  messages: number;
  draft: number;
  memory_recall: number;
  system_overhead: number;
}

export interface ChatContextUsage {
  usage_ratio: number;
  used_tokens: number;
  max_tokens: number;
  usage_percent: number;
  breakdown: ContextUsageBreakdown;
  message_count: number;
  model_id?: string | null;
}

const DEFAULT_MAX_CHARS = 128_000 * 4;

/** Client-side fallback when the API is unavailable. */
export function estimateContextUsage(
  messages: ChatMessage[],
  draft = "",
  maxChars = DEFAULT_MAX_CHARS
): ChatContextUsage {
  const messageChars = messages.reduce((n, m) => n + m.content.length, 0);
  const draftChars = draft.trim().length;
  const usedChars = messageChars + draftChars;
  const usedTokens = Math.ceil(usedChars / 4);
  const maxTokens = Math.ceil(maxChars / 4);
  const ratio = Math.min(1, usedChars / maxChars);

  return {
    usage_ratio: ratio,
    used_tokens: usedTokens,
    max_tokens: maxTokens,
    usage_percent: Math.round(ratio * 100),
    breakdown: {
      messages: Math.ceil(messageChars / 4),
      draft: Math.ceil(draftChars / 4),
      memory_recall: 0,
      system_overhead: 0,
    },
    message_count: messages.length,
  };
}

export function formatTokenCount(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}k`;
  return String(tokens);
}
