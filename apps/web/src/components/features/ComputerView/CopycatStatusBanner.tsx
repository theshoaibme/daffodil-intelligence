import { motion } from "framer-motion";
import { AlertTriangle, Square, Timer } from "lucide-react";
import { modeSpring } from "@lib";
import { useEffect, useState } from "react";

interface CopycatStatusBannerProps {
  message?: string | null;
  onStop: () => void;
  currentAction?: number | null;
  totalActions?: number | null;
}

export function CopycatStatusBanner({
  message,
  onStop,
  currentAction,
  totalActions,
}: CopycatStatusBannerProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setElapsed((v) => v + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const progress =
    currentAction != null && totalActions != null && totalActions > 0
      ? Math.round((currentAction / totalActions) * 100)
      : null;

  return (
    <div className="absolute top-0 left-0 right-0 z-[60] flex justify-center pointer-events-none">
      <motion.div
        initial={{ opacity: 0, y: -16, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -12, scale: 0.96 }}
        transition={modeSpring}
        className="mt-4 flex items-center gap-3 bg-error text-white px-5 py-3 rounded-2xl shadow-lg border border-error/80 pointer-events-auto"
      >
        <AlertTriangle size={20} className="shrink-0 animate-pulse" />

        <div className="min-w-0">
          <p className="text-sm font-bold tracking-wide">CopyCat is running</p>
          <p className="text-xs opacity-90 truncate">
            {message || "Mouse and keyboard are disabled for your safety"}
          </p>
        </div>

        {/* Progress indicator */}
        {progress !== null && (
          <div className="flex items-center gap-2 ml-1">
            <div className="w-16 h-1.5 rounded-full bg-white/20 overflow-hidden">
              <div
                className="h-full rounded-full bg-white/80 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-[10px] font-mono opacity-80 whitespace-nowrap">
              {currentAction}/{totalActions}
            </span>
          </div>
        )}

        {/* Elapsed timer */}
        <div className="flex items-center gap-1 text-[10px] font-mono opacity-75 ml-1">
          <Timer size={10} />
          {formatTime(elapsed)}
        </div>

        <button
          type="button"
          onClick={onStop}
          className="ml-2 flex items-center gap-1 px-3 py-1.5 rounded-full bg-white/15 hover:bg-white/25 text-xs font-medium transition-colors"
        >
          <Square size={12} fill="currentColor" />
          Stop
        </button>
      </motion.div>
    </div>
  );
}
