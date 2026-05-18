import { ImagePlus, Sparkles, ArrowUp } from "lucide-react";

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

export function SendButton({ onClick }: { onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className="w-10 h-10 flex items-center justify-center bg-primary text-on-primary rounded-full hover:opacity-90 transition-all font-bold cursor-pointer border-0 outline-none"
    >
      <ArrowUp size={22} strokeWidth={3} />
    </button>
  );
}
