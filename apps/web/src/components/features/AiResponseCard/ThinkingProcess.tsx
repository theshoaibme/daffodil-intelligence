import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface ThinkingStep {
  id: string;
  title: string;
  status: "pending" | "active" | "success";
}

interface ThinkingProcessProps {
  isThinking: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
  thinkingText?: string;
  /** @deprecated Timing is not shown in the UI. */
  thinkingMs?: number | null;
  /** @deprecated Steps live in Task manager — not shown here. */
  steps?: ThinkingStep[];
}

export function ThinkingProcess({
  isThinking,
  isExpanded,
  onToggleExpand,
  thinkingText = "",
}: ThinkingProcessProps) {
  const hasThinkingText = thinkingText.trim().length > 0;
  if (!isThinking && !hasThinkingText) {
    return null;
  }

  const headerLabel = isThinking ? "Thinking" : "Thought";

  return (
    <div className="flex w-full flex-col gap-1">
      <button
        type="button"
        onClick={onToggleExpand}
        className="group flex w-fit max-w-full items-center gap-1 border-0 bg-transparent p-0 text-left outline-none cursor-pointer"
        aria-expanded={isExpanded}
      >
        <span
          className={`truncate text-xs font-medium ${
            isThinking ? "thinking-shimmer" : "text-on-surface-variant"
          }`}
        >
          {headerLabel}
        </span>
        <motion.span
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="shrink-0 text-on-surface-variant/60 transition-colors group-hover:text-on-surface-variant"
        >
          <ChevronDown size={14} strokeWidth={2} />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {isExpanded && (hasThinkingText || isThinking) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <p className="max-h-[min(140px,20dvh)] overflow-y-auto no-scrollbar pt-1 text-xs leading-relaxed text-on-surface-variant/80 whitespace-pre-wrap font-normal select-text">
              {hasThinkingText ? thinkingText : null}
              {isThinking && (
                <span
                  className={`inline-block align-middle ${hasThinkingText ? "w-1 h-3.5 ml-0.5 bg-on-surface-variant/35 rounded-sm animate-pulse" : "thinking-shimmer"}`}
                  aria-hidden={!hasThinkingText}
                >
                  {!hasThinkingText ? "Gathering thoughts…" : null}
                </span>
              )}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
