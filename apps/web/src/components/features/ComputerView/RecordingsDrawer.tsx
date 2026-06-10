import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Play,
  Trash2,
  Clock,
  Hash,
  SkipForward,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import { modeSpring } from "@lib";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface RecordingEntry {
  name: string;
  created_at: number;
  duration: number;
  action_count: number;
  file: string;
}

interface RecordingsDrawerProps {
  open: boolean;
  onClose: () => void;
  onReplay: (name: string, speed: number, skipMouseMoves: boolean) => void;
  isReplaying: boolean;
}

const SPEEDS = [
  { label: "0.5×", value: 0.5 },
  { label: "1×", value: 1 },
  { label: "2×", value: 2 },
  { label: "5×", value: 5 },
  { label: "10×", value: 10 },
];

export function RecordingsDrawer({
  open,
  onClose,
  onReplay,
  isReplaying,
}: RecordingsDrawerProps) {
  const [recordings, setRecordings] = useState<RecordingEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSpeed, setSelectedSpeed] = useState(2);
  const [skipMouseMoves, setSkipMouseMoves] = useState(true);

  const fetchRecordings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/computer/record/list`);
      const data = await res.json();
      setRecordings(data.recordings || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) fetchRecordings();
  }, [open, fetchRecordings]);

  const handleDelete = useCallback(
    async (name: string) => {
      await fetch(`${API_BASE}/api/computer/record/${name}`, {
        method: "DELETE",
      });
      setRecordings((prev) => prev.filter((r) => r.name !== name));
    },
    []
  );

  const formatDate = (ts: number) => {
    const d = new Date(ts * 1000);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDuration = (s: number) => {
    if (s < 60) return `${Math.round(s)}s`;
    const m = Math.floor(s / 60);
    const sec = Math.round(s % 60);
    return `${m}m ${sec}s`;
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/20 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            transition={modeSpring}
            className="fixed right-0 top-0 bottom-0 z-[71] w-80 max-w-[90vw] bg-surface-container-low border-l border-outline-variant/50 shadow-xl flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-outline-variant/30">
              <h3 className="text-sm font-medium text-on-surface">
                Recordings
              </h3>
              <button
                type="button"
                onClick={onClose}
                className="p-1 rounded-full hover:bg-surface-container-high text-on-surface-variant"
              >
                <X size={16} />
              </button>
            </div>

            {/* Replay settings */}
            <div className="px-4 py-3 border-b border-outline-variant/20 space-y-3">
              {/* Speed selector */}
              <div>
                <label className="text-[10px] uppercase tracking-wider text-on-surface-variant font-medium mb-1 block">
                  Playback Speed
                </label>
                <div className="flex gap-1">
                  {SPEEDS.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => setSelectedSpeed(s.value)}
                      className={`flex-1 px-1 py-1 text-xs font-medium rounded-lg transition-colors ${
                        selectedSpeed === s.value
                          ? "bg-primary text-on-primary"
                          : "text-on-surface-variant hover:bg-surface-container-high"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Skip mouse moves */}
              <button
                type="button"
                onClick={() => setSkipMouseMoves((v) => !v)}
                className="flex items-center gap-2 w-full text-xs"
              >
                {skipMouseMoves ? (
                  <ToggleRight size={20} className="text-primary" />
                ) : (
                  <ToggleLeft size={20} className="text-on-surface-variant" />
                )}
                <span className="text-on-surface-variant">
                  <SkipForward size={12} className="inline mr-1" />
                  Skip mouse movements
                </span>
              </button>
            </div>

            {/* Recordings list */}
            <div className="flex-1 overflow-y-auto custom-scrollbar px-3 py-2">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                </div>
              ) : recordings.length === 0 ? (
                <div className="text-center py-8 text-xs text-on-surface-variant/60">
                  No recordings yet. Use the record button to create one.
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {recordings.map((rec) => (
                    <div
                      key={rec.name}
                      className="bg-surface-container border border-outline-variant/30 rounded-xl p-3 space-y-2"
                    >
                      <div className="flex items-start justify-between">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-on-surface truncate">
                            {rec.name}
                          </p>
                          <p className="text-[10px] text-on-surface-variant">
                            {formatDate(rec.created_at)}
                          </p>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex items-center gap-3 text-[10px] text-on-surface-variant">
                        <span className="flex items-center gap-1">
                          <Clock size={10} />
                          {formatDuration(rec.duration)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Hash size={10} />
                          {rec.action_count} actions
                        </span>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() =>
                            onReplay(rec.name, selectedSpeed, skipMouseMoves)
                          }
                          disabled={isReplaying}
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium bg-primary text-on-primary rounded-lg disabled:opacity-50 hover:opacity-90 transition-opacity"
                        >
                          <Play size={12} fill="currentColor" />
                          Play
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(rec.name)}
                          className="p-1.5 rounded-lg text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors"
                          aria-label={`Delete ${rec.name}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
