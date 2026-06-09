import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  formatTokenCount,
  type ChatContextUsage,
} from "@lib";

interface ContextUseRingProps {
  context: ChatContextUsage;
  size?: number;
}

function ringColor(percent: number): string {
  if (percent >= 90) return "text-red-400";
  if (percent >= 70) return "text-amber-400";
  return "text-on-surface-variant/80";
}

export function ContextUseRing({ context, size = 20 }: ContextUseRingProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const percent = context.usage_percent;
  const ratio = context.usage_ratio;
  const clamped = Math.min(1, Math.max(0, ratio));
  const strokeWidth = 2;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped);
  const colorClass = ringColor(percent);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const breakdownRows = [
    { label: "Messages", value: context.breakdown.messages },
    { label: "Draft", value: context.breakdown.draft },
    { label: "Memory", value: context.breakdown.memory_recall },
    { label: "System", value: context.breakdown.system_overhead },
  ].filter((row) => row.value > 0 || row.label === "Messages");

  return (
    <div className="relative shrink-0" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={`Context used: ${percent}%`}
        aria-expanded={open}
        className="flex items-center justify-center rounded-full border-0 outline-none bg-transparent cursor-pointer p-0.5 hover:bg-surface-container-highest/50 transition-colors"
      >
        <svg width={size} height={size} className={`-rotate-90 ${colorClass}`}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-on-surface-variant/20"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={colorClass}
          />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 6 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className="absolute bottom-full right-0 mb-2 w-52 glass-gradient-panel border border-outline-variant/40 rounded-xl shadow-md z-[60] p-3"
          >
            <p className="text-xs font-medium text-on-surface mb-2">Context usage</p>
            <p className="text-lg font-semibold text-on-surface leading-none mb-0.5">
              {percent}%
            </p>
            <p className="text-[11px] text-on-surface-variant mb-3">
              {formatTokenCount(context.used_tokens)} / {formatTokenCount(context.max_tokens)} tokens
            </p>

            <div className="space-y-1.5">
              {breakdownRows.map((row) => {
                const rowRatio =
                  context.used_tokens > 0 ? row.value / context.used_tokens : 0;
                return (
                  <div key={row.label}>
                    <div className="flex justify-between text-[11px] text-on-surface-variant mb-0.5">
                      <span>{row.label}</span>
                      <span>{formatTokenCount(row.value)}</span>
                    </div>
                    <div className="h-1 rounded-full bg-surface-container-highest overflow-hidden">
                      <div
                        className="h-full rounded-full bg-on-surface-variant/50"
                        style={{ width: `${Math.max(4, rowRatio * 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <p className="text-[10px] text-on-surface-variant/70 mt-2.5">
              {context.message_count} message{context.message_count === 1 ? "" : "s"}
              {context.model_id ? ` · ${context.model_id}` : ""}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
