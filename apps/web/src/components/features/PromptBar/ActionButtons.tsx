import { Link, Sparkles, ArrowUp, Mic } from "lucide-react";

const promptIconButtonClass =
  "w-8 h-8 flex items-center justify-center text-on-surface-variant hover:text-on-surface rounded-full transition-all cursor-pointer border-0 outline-none bg-transparent";

export function FileAttachmentButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Attach file"
      title="Attach file"
      className={promptIconButtonClass}
    >
      <Link size={16} />
    </button>
  );
}

export function SparklesButton({ onSparklesClick }: { onSparklesClick?: () => void }) {
  return (
    <button
      onClick={onSparklesClick}
      className="w-10 h-10 flex items-center justify-center bg-primary/10 text-primary hover:bg-primary/20 rounded-full transition-all cursor-pointer border-0 outline-none"
    >
      <Sparkles size={20} fill="currentColor" />
    </button>
  );
}

export function MicButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Record voice message"
      title="Record voice"
      className="w-8 h-8 flex items-center justify-center rounded-full transition-all border-0 outline-none bg-[#5a5a5a] text-[#1a1a1a] hover:bg-[#666666] cursor-pointer"
    >
      <Mic size={16} strokeWidth={2.5} />
    </button>
  );
}

/** @deprecated Use MicButton */
export const LiveVoiceButton = MicButton;

export function SendButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Send message"
      title="Send"
      className="w-8 h-8 flex items-center justify-center rounded-full transition-all border-0 outline-none cursor-pointer bg-on-surface text-surface-container-lowest hover:opacity-90 dark:bg-on-surface dark:text-background dark:hover:opacity-90 shadow-sm"
    >
      <ArrowUp size={17} strokeWidth={2.75} />
    </button>
  );
}

export function StopButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Stop generating"
      title="Stop"
      className="w-8 h-8 flex items-center justify-center rounded-full transition-all border-0 outline-none cursor-pointer bg-on-surface text-surface-container-lowest hover:opacity-90 dark:bg-on-surface dark:text-background dark:hover:opacity-90 shadow-sm"
    >
      <span className="block w-2.5 h-2.5 rounded-[2px] bg-current" />
    </button>
  );
}
