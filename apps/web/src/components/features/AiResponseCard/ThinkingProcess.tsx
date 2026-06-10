export interface ThinkingStep {
  id: string;
  title: string;
  status: "pending" | "active" | "success";
}

interface ThinkingProcessProps {
  isThinking: boolean;
  thinkingText?: string;
  thinkingMs?: number | null;
  /** @deprecated Steps live in Task manager — not shown here. */
  steps?: ThinkingStep[];
  /** @deprecated Thinking is always expanded. */
  isExpanded?: boolean;
  /** @deprecated Thinking is always expanded. */
  onToggleExpand?: () => void;
}

function formatThinkingDuration(ms: number | null | undefined): string | null {
  if (ms == null || ms < 0) return null;
  if (ms < 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 1000)}s`;
}

export function ThinkingProcess({
  isThinking,
  thinkingText = "",
  thinkingMs = null,
}: ThinkingProcessProps) {
  const hasThinkingText = thinkingText.trim().length > 0;
  if (!isThinking && !hasThinkingText) {
    return null;
  }

  const duration = formatThinkingDuration(thinkingMs);
  const headerLabel = isThinking ? "Thinking" : "Thought";

  return (
    <div className="flex w-full flex-col gap-1.5">
      <p className="text-xs font-medium text-on-surface-variant/60">
        {headerLabel}
        {duration ? <span className="font-normal"> · {duration}</span> : null}
      </p>

      <div className="text-xs leading-relaxed text-on-surface-variant/70 whitespace-pre-wrap font-normal select-text">
        {hasThinkingText ? thinkingText : null}
        {isThinking && !hasThinkingText ? (
          <span className="thinking-shimmer">Gathering thoughts…</span>
        ) : null}
        {isThinking && hasThinkingText ? (
          <span
            className="inline-block w-1 h-3.5 ml-0.5 bg-on-surface-variant/30 rounded-sm animate-pulse align-middle"
            aria-hidden
          />
        ) : null}
      </div>
    </div>
  );
}
