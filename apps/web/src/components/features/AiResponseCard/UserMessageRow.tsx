import { useState } from "react";
import { Check, Copy, Pencil } from "lucide-react";

interface UserMessageRowProps {
  content: string;
  isPanel?: boolean;
  disabled?: boolean;
  onEdit?: () => void;
}

export function UserMessageRow({
  content,
  isPanel = false,
  disabled = false,
  onEdit,
}: UserMessageRowProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy message: ", err);
    }
  };

  return (
    <div className="group/user flex justify-end items-start gap-1.5 w-full">
      <div
        className={`flex items-center gap-0.5 shrink-0 pt-2 transition-opacity ${
          disabled
            ? "opacity-0 pointer-events-none"
            : "opacity-0 group-hover/user:opacity-100 group-focus-within/user:opacity-100"
        }`}
      >
        <button
          type="button"
          onClick={handleCopy}
          title="Copy message"
          aria-label="Copy message"
          className="p-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors border-0 bg-transparent cursor-pointer outline-none"
        >
          {copied ? (
            <Check size={14} className="text-primary stroke-[3]" />
          ) : (
            <Copy size={14} />
          )}
        </button>
        {onEdit && (
          <button
            type="button"
            onClick={onEdit}
            title="Edit message"
            aria-label="Edit message"
            className="p-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors border-0 bg-transparent cursor-pointer outline-none"
          >
            <Pencil size={14} />
          </button>
        )}
      </div>

      <div
        className={`rounded-3xl chat-bubble-user px-3 py-2 sm:px-3.5 sm:py-2.5 ${
          isPanel ? "max-w-[92%]" : "max-w-[88%] sm:max-w-[78%]"
        }`}
      >
        <p className="text-sm text-on-surface whitespace-pre-wrap break-words leading-relaxed">
          {content}
        </p>
      </div>
    </div>
  );
}
