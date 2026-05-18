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
}

export function ThinkingProcess({
  isThinking,
  steps,
  isExpanded,
  onToggleExpand,
}: ThinkingProcessProps) {
  return (
    <div className="flex flex-col gap-2.5 w-full">
      {/* Dynamic Gemini-Inspired Animated Thinking Bar */}
      {isThinking && (
        <div className="relative w-full h-1 rounded-full overflow-hidden bg-primary/10 select-none">
          <motion.div
            className="absolute top-0 bottom-0 h-full rounded-full bg-gradient-to-r from-primary via-secondary to-primary"
            style={{ width: "40%" }}
            animate={{ left: ["-40%", "110%"] }}
            transition={{
              duration: 1.6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        </div>
      )}

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
          <span>
            {isThinking
              ? "Thinking..."
              : `Steps executed (${steps.filter((s) => s.status === "success").length})`}
          </span>
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
            className="w-full bg-surface-container-highest/65 rounded-2xl shadow-md overflow-hidden p-3 flex flex-col gap-2"
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
            <div className="flex flex-col gap-1.5">
              {steps.map((step) => (
                <div
                  key={step.id}
                  className={`flex items-center gap-2.5 p-2 rounded-xl transition-colors ${
                    step.status === "active"
                      ? "bg-primary/10 text-primary"
                      : "text-on-surface-variant hover:bg-surface-container-high/60"
                  }`}
                >
                  {step.status === "success" && (
                    <Check size={13} className="text-primary stroke-[3.5] flex-shrink-0" />
                  )}
                  {step.status === "active" && (
                    <Loader2 size={13} className="animate-spin text-primary flex-shrink-0" />
                  )}
                  {step.status === "pending" && (
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-outline-variant/40 flex-shrink-0" />
                  )}
                  <span className="text-xs font-medium leading-none">{step.title}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
