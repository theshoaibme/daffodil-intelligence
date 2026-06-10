import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";
import { cleanThinkingText } from "@lib/thinkingText";

export interface ThinkingStep {
  id: string;
  title: string;
  status: "pending" | "active" | "success";
}

interface ThinkingProcessProps {
  isThinking: boolean;
  thinkingText?: string;
  thinkingMs?: number | null;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  /** @deprecated Steps live in Task manager — not shown here. */
  steps?: ThinkingStep[];
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
  isExpanded,
  onToggleExpand,
}: ThinkingProcessProps) {
  const displayText = cleanThinkingText(thinkingText);
  const hasThinkingText = displayText.length > 0;
  const [internalExpanded, setInternalExpanded] = useState(true);
  const controlled = isExpanded !== undefined && onToggleExpand !== undefined;
  const expanded = controlled ? isExpanded : internalExpanded;

  useEffect(() => {
    if (!controlled && (isThinking || hasThinkingText)) {
      setInternalExpanded(true);
    }
  }, [controlled, isThinking, hasThinkingText]);

  if (!isThinking && !hasThinkingText) {
    return null;
  }

  const duration = formatThinkingDuration(thinkingMs);
  const headerLabel = isThinking ? "Thinking" : "Thought";

  const toggle = () => {
    if (controlled) {
      onToggleExpand();
      return;
    }
    setInternalExpanded((open) => !open);
  };

  return (
    <div className="flex w-full flex-col gap-1 select-text">
      <button
        type="button"
        onClick={toggle}
        className="group flex w-fit max-w-full items-center gap-1 border-0 bg-transparent p-0 text-left outline-none cursor-pointer"
        aria-expanded={expanded}
      >
        <span
          className={`text-xs font-medium ${
            isThinking ? "thinking-shimmer" : "text-on-surface-variant"
          }`}
        >
          {headerLabel}
          {duration ? ` · ${duration}` : null}
        </span>
        <motion.span
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="shrink-0 text-on-surface-variant/60 transition-colors group-hover:text-on-surface-variant"
        >
          <ChevronDown size={14} strokeWidth={2} />
        </motion.span>
      </button>

      {expanded && hasThinkingText ? (
        <p className="thinking-message text-xs leading-relaxed whitespace-pre-wrap break-words font-normal">
          {displayText}
        </p>
      ) : null}
    </div>
  );
}
