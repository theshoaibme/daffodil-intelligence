import { ImagePlus, Sparkles, ArrowUp, Loader2, Mic } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../../lib/routes";

export function ImageAttachmentButton({ onImageClick }: { onImageClick?: () => void }) {
  return (
    <button 
      onClick={onImageClick}
      className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest rounded-full transition-all cursor-pointer border-0 outline-none"
    >
      <ImagePlus size={22} />
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

export function LiveVoiceButton() {
  const navigate = useNavigate();
  return (
    <button 
      onClick={() => navigate(ROUTES.live)}
      className="w-10 h-10 flex items-center justify-center bg-secondary-container/50 text-secondary hover:bg-secondary-container rounded-full transition-all cursor-pointer border-0 outline-none"
      title="Live Voice"
    >
      <Mic size={20} />
    </button>
  );
}

export function SendButton({ onClick, disabled, loading }: { onClick?: () => void; disabled?: boolean; loading?: boolean }) {
  return (
    <button 
      onClick={disabled || loading ? undefined : onClick}
      disabled={disabled || loading}
      className={`w-8 h-8 flex items-center justify-center rounded-full transition-all font-bold border-0 outline-none shadow-sm ${
        disabled || loading
          ? "bg-surface-container-highest text-on-surface-variant/30 cursor-not-allowed shadow-none" 
          : "bg-primary text-on-primary hover:opacity-90 hover:shadow-md cursor-pointer"
      }`}
    >
      {loading ? (
        <Loader2 size={16} className="animate-spin" />
      ) : (
        <ArrowUp size={18} strokeWidth={3} />
      )}
    </button>
  );
}
