import { Check, ChevronDown, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface ThinkingStep {
  id: string;
  title: string;
  status: "pending" | "active" | "success";
}

interface ThinkingProcessProps {
  isThinking: boolean;
  steps: ThinkingStep[];
  isExpanded: boolean;
  onToggleExpand: () => void;
  thinkingText?: string;
  thinkingMs?: number | null;
}

function formatDuration(ms?: number | null): string | null {
  if (ms == null || ms <= 0) return null;
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const rem = Math.round(seconds % 60);
  return `${mins}m ${rem}s`;
}

export function ThinkingProcess({
  isThinking,
  steps,
  isExpanded,
  onToggleExpand,
  thinkingText = "",
  thinkingMs = null,
}: ThinkingProcessProps) {
  const hasThinkingText = thinkingText.trim().length > 0;
  if ((!steps || steps.length === 0) && !isThinking && !hasThinkingText) {
    return null;
  }

  const duration = formatDuration(thinkingMs);
  const completedSteps = steps.filter((s) => s.status === "success").length;

  let headerLabel: string;
  if (isThinking) {
    headerLabel = duration ? `Thinking ${duration}` : "Thinking...";
  } else if (duration) {
    headerLabel = `Thought for ${duration}`;
  } else {
    headerLabel = `Steps executed (${completedSteps})`;
  }

  return (
    <div className="flex flex-col gap-2.5 w-full">

      {/* Accordion Trigger Row */}
      <div className="flex items-center justify-between w-full relative">
        <button
          onClick={onToggleExpand}
          className="flex items-center gap-2 bg-surface-container-high hover:bg-surface-container-highest rounded-full pl-2 pr-4 py-1.5 cursor-pointer transition-all duration-200 w-fit text-left outline-none text-xs font-semibold text-on-surface-variant shadow-sm"
        >
          {isThinking ? (
            <Loader2 size={13} className="animate-spin text-primary flex-shrink-0" />
          ) : (
            <div className="w-3.5 h-3.5 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Check size={10} className="text-primary stroke-[3]" />
            </div>
          )}
          <span>{headerLabel}</span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="flex-shrink-0 ml-0.5"
          >
            <ChevronDown size={13} />
          </motion.div>
        </button>

        {/* 2 Dots Capsule - moved from header to steps executed right side */}
        <div className="bg-on-surface rounded-full px-2.5 py-1 flex items-center justify-center gap-1 w-[46px] h-[22px] flex-shrink-0 shadow-sm">
          <div className="w-1.5 h-1.5 rounded-full bg-surface"></div>
          <div className="w-1.5 h-1.5 rounded-full bg-surface"></div>
        </div>
      </div>

      {/* Accordion Steps List Drawer */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: "auto", marginTop: 8 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="w-full max-h-[min(160px,22dvh)] overflow-y-auto no-scrollbar bg-surface-container-highest/65 rounded-2xl shadow-md p-3 flex flex-col gap-2"
          >
            <div className="text-[10px] font-bold text-on-surface-variant/60 tracking-wider px-1 flex items-center h-4">
              <span>Thinking</span>
              <span className="flex items-center gap-[3px] ml-1 h-full pt-[3px]">
                <motion.span
                  className="w-[3px] h-[3px] rounded-full bg-on-surface-variant/60 flex-shrink-0"
                  animate={{ y: [0, -2.5, 0], opacity: [0.35, 1, 0.35] }}
                  transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut", delay: 0 }}
                />
                <motion.span
                  className="w-[3px] h-[3px] rounded-full bg-on-surface-variant/60 flex-shrink-0"
                  animate={{ y: [0, -2.5, 0], opacity: [0.35, 1, 0.35] }}
                  transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut", delay: 0.15 }}
                />
                <motion.span
                  className="w-[3px] h-[3px] rounded-full bg-on-surface-variant/60 flex-shrink-0"
                  animate={{ y: [0, -2.5, 0], opacity: [0.35, 1, 0.35] }}
                  transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
                />
              </span>
            </div>
            {hasThinkingText && (
              <p className="text-xs leading-relaxed text-on-surface-variant/70 whitespace-pre-wrap font-normal px-1 select-text">
                {thinkingText}
                {isThinking && (
                  <span
                    className="inline-block w-1.5 h-3 ml-0.5 bg-on-surface-variant/40 rounded-sm animate-pulse align-middle"
                    aria-hidden
                  />
                )}
              </p>
            )}
            {steps.length > 0 && (
              <div className="flex flex-col gap-1.5">
                {steps.map((step) => {
                  const isSystem = step.id.startsWith("status:") || step.id === "model";
                  return (
                    <div
                      key={step.id}
                      className={`flex items-center gap-2.5 p-2 rounded-xl transition-colors ${
                        step.status === "active"
                          ? "bg-primary/10 text-primary"
                          : isSystem
                            ? "text-on-surface-variant/75 italic"
                            : "text-on-surface-variant hover:bg-surface-container-high/60"
                      }`}
                    >
                      {step.status === "success" && !isSystem && (
                        <Check size={13} className="text-primary stroke-[3.5] flex-shrink-0" />
                      )}
                      {step.status === "success" && isSystem && (
                        <div className="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40 flex-shrink-0 ml-1" />
                      )}
                      {step.status === "active" && (
                        <Loader2 size={13} className="animate-spin text-primary flex-shrink-0" />
                      )}
                      {step.status === "pending" && (
                        <div className="w-3.5 h-3.5 rounded-full border-2 border-outline-variant/40 flex-shrink-0" />
                      )}
                      <span className="text-xs font-medium leading-snug">{step.title}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
