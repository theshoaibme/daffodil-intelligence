import { Mic, X } from "lucide-react";
import { WaveformBars } from "./WaveformBars";

interface VoiceRecordingBadgeProps {
  durationMs: number;
  onDiscard: () => void;
}

function formatDuration(ms: number): string {
  const totalSec = Math.max(0, Math.round(ms / 1000));
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}:${sec.toString().padStart(2, "0")}`;
}

export function VoiceRecordingBadge({ durationMs, onDiscard }: VoiceRecordingBadgeProps) {
  const previewLevels = [0.25, 0.55, 0.85, 0.45, 0.3];

  return (
    <div className="group relative flex w-full max-w-[50%] min-w-0 items-center gap-2 rounded-2xl border border-outline-variant/30 bg-surface-container-highest/60 px-3 py-2 min-h-[36px]">
      <Mic size={14} className="shrink-0 text-on-surface-variant" />
      <WaveformBars levels={previewLevels} className="opacity-90" />
      <span className="text-xs text-on-surface-variant tabular-nums">{formatDuration(durationMs)}</span>
      <button
        type="button"
        onClick={onDiscard}
        aria-label="Discard voice recording"
        className="absolute right-1.5 top-1/2 -translate-y-1/2 flex h-6 w-6 items-center justify-center rounded-full bg-surface-container-high text-on-surface opacity-0 group-hover:opacity-100 transition-opacity border-0 outline-none cursor-pointer"
      >
        <X size={14} />
      </button>
    </div>
  );
}
