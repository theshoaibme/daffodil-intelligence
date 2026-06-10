import { useRef, useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mouse,
  Keyboard,
  Camera,
  Info,
  Zap,
  Trash2,
  Download,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { ActionLogEntry } from "@hooks";
import { modeSpring } from "@lib";

interface ActionFeedProps {
  actionLog: ActionLogEntry[];
  onClear?: () => void;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
  mouse_move: <Mouse size={12} className="text-blue-500" />,
  mouse_click: <Mouse size={12} className="text-blue-600" />,
  keyboard_type: <Keyboard size={12} className="text-green-500" />,
  hotkey: <Keyboard size={12} className="text-green-600" />,
  scroll: <Mouse size={12} className="text-indigo-500" />,
  screenshot: <Camera size={12} className="text-orange-500" />,
  info: <Info size={12} className="text-on-surface-variant" />,
};

const ACTION_COLORS: Record<string, string> = {
  mouse_move: "border-l-blue-400/50",
  mouse_click: "border-l-blue-500",
  keyboard_type: "border-l-green-500",
  hotkey: "border-l-green-600",
  scroll: "border-l-indigo-500",
  screenshot: "border-l-orange-500",
  info: "border-l-outline-variant",
};

function formatTimestamp(ts: number) {
  const d = new Date(ts);
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ActionFeed({ actionLog, onClear }: ActionFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to latest entry
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0; // newest at top
    }
  }, [actionLog, autoScroll]);

  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;
    const { scrollTop } = scrollRef.current;
    setAutoScroll(scrollTop < 10);
  }, []);

  const exportLog = useCallback(() => {
    const text = actionLog
      .map(
        (e) =>
          `[${formatTimestamp(e.timestamp)}] ${e.type}: ${e.description}${
            e.x != null ? ` (${e.x}, ${e.y})` : ""
          }`
      )
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `copycat-actions-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [actionLog]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 16 }}
      transition={modeSpring}
      className="bg-surface-container border border-outline-variant/50 rounded-2xl overflow-hidden shadow-sm"
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-surface-container-high/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Zap size={14} className="text-primary" />
          <span className="text-xs font-medium text-on-surface">
            Actions
          </span>
          {actionLog.length > 0 && (
            <span className="px-1.5 py-0.5 text-[9px] font-medium rounded-full bg-primary/10 text-primary">
              {actionLog.length}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronDown size={14} className="text-on-surface-variant" />
        ) : (
          <ChevronUp size={14} className="text-on-surface-variant" />
        )}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Action buttons */}
            {actionLog.length > 0 && (
              <div className="flex items-center gap-1 px-3 pb-1">
                <button
                  type="button"
                  onClick={onClear}
                  className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-on-surface-variant hover:text-on-surface rounded-full hover:bg-surface-container-high transition-colors"
                >
                  <Trash2 size={10} />
                  Clear
                </button>
                <button
                  type="button"
                  onClick={exportLog}
                  className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-on-surface-variant hover:text-on-surface rounded-full hover:bg-surface-container-high transition-colors"
                >
                  <Download size={10} />
                  Export
                </button>
              </div>
            )}

            {/* Log entries */}
            <div
              ref={scrollRef}
              onScroll={handleScroll}
              className="max-h-48 overflow-y-auto custom-scrollbar px-2 pb-2"
            >
              {actionLog.length === 0 ? (
                <div className="text-center py-4 text-xs text-on-surface-variant/60">
                  No actions yet
                </div>
              ) : (
                <div className="flex flex-col gap-0.5">
                  {actionLog.map((entry, i) => (
                    <div
                      key={`${entry.timestamp}-${i}`}
                      className={`flex items-start gap-2 px-2 py-1 rounded-lg border-l-2 ${
                        ACTION_COLORS[entry.type] || "border-l-outline-variant"
                      } bg-surface-container-low/50`}
                    >
                      <span className="mt-0.5 shrink-0">
                        {ACTION_ICONS[entry.type] || <Info size={12} />}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-on-surface truncate">
                          {entry.description}
                        </p>
                        <div className="flex items-center gap-2 text-[9px] text-on-surface-variant/70 font-mono">
                          <span>{formatTimestamp(entry.timestamp)}</span>
                          {entry.x != null && (
                            <span>
                              ({entry.x}, {entry.y})
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
