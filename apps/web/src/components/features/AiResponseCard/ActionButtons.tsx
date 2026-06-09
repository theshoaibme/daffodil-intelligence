import { useState } from "react";
import { Copy, Check, Share2, Maximize2, Minimize2 } from "lucide-react";

interface ActionButtonsProps {
  textToCopy: string;
  onFullView?: () => void;
  onSidePanel?: () => void;
  showFullView?: boolean;
  showSidePanel?: boolean;
  showCopyActions?: boolean;
  embedded?: boolean;
  footer?: boolean;
}

export function ActionButtons({
  textToCopy,
  onFullView,
  onSidePanel,
  showFullView = true,
  showSidePanel = false,
  showCopyActions = true,
  embedded = false,
  footer = false,
}: ActionButtonsProps) {
  const [copied, setCopied] = useState(false);
  const [shared, setShared] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const handleShare = () => {
    setShared(true);
    setTimeout(() => setShared(false), 2500);
    alert("Share link copied to clipboard!");
  };

  return (
    <div
      className={`flex items-center flex-shrink-0 select-none ${
        footer
          ? "justify-end w-full"
          : embedded
            ? "justify-start gap-1 pt-2"
            : "justify-between pt-4 mt-auto"
      }`}
    >
      {showCopyActions && (
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleCopy}
            title="Copy response"
            className="p-2 hover:bg-surface-container-high rounded-full transition-all cursor-pointer text-on-surface-variant flex items-center justify-center border border-transparent hover:border-outline-variant/30 outline-none"
          >
            {copied ? (
              <Check size={14} className="text-primary stroke-[3.5]" />
            ) : (
              <Copy size={14} />
            )}
          </button>
          <button
            onClick={handleShare}
            title="Share action link"
            className="p-2 hover:bg-surface-container-high rounded-full transition-all cursor-pointer text-on-surface-variant flex items-center justify-center border border-transparent hover:border-outline-variant/30 outline-none relative"
          >
            {shared ? (
              <Check size={14} className="text-primary stroke-[3.5]" />
            ) : (
              <Share2 size={14} />
            )}
          </button>
        </div>
      )}

      {showSidePanel && onSidePanel && (
        <button
          type="button"
          onClick={onSidePanel}
          className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-surface-container-high rounded-full transition-all cursor-pointer text-xs font-semibold text-on-surface-variant border border-outline-variant/20 hover:border-outline-variant/40 outline-none shadow-sm"
        >
          <Minimize2 size={12} />
          <span>Side panel</span>
        </button>
      )}
      {showFullView && onFullView && (
        <button
          type="button"
          onClick={onFullView}
          className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-surface-container-high rounded-full transition-all cursor-pointer text-xs font-semibold text-on-surface-variant border border-outline-variant/20 hover:border-outline-variant/40 outline-none shadow-sm"
        >
          <Maximize2 size={12} />
          <span>Full View</span>
        </button>
      )}
    </div>
  );
}
