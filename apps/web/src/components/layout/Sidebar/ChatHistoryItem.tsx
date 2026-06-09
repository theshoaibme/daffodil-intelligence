import { useEffect, useRef, useState } from "react";
import { MessageSquare, MoreHorizontal, Trash2, Share2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { formatHistoryDate } from "@lib";

interface ChatHistoryItemProps {
  id: string;
  title: string;
  updatedAt: string;
  active?: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onShare: () => void;
}

export function ChatHistoryItem({
  title,
  updatedAt,
  active = false,
  onSelect,
  onDelete,
  onShare,
}: ChatHistoryItemProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  return (
    <div ref={containerRef} className="relative group/item">
      <button
        type="button"
        onClick={onSelect}
        className={`flex items-center gap-3 p-2 pr-9 rounded-xl cursor-pointer transition-all text-left w-full border-0 ${
          active
            ? "bg-surface-container-highest text-on-surface"
            : "bg-transparent text-on-surface hover:bg-surface-container-high"
        }`}
      >
        <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center border border-outline-variant/10 flex-shrink-0">
          <MessageSquare size={18} className="text-on-surface-variant" strokeWidth={1.75} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm truncate font-medium">{title}</p>
          <p className="text-[11px] text-on-surface-variant truncate">
            {formatHistoryDate(updatedAt)}
          </p>
        </div>
      </button>

      <button
        type="button"
        aria-label="Chat options"
        onClick={(event) => {
          event.stopPropagation();
          setMenuOpen((open) => !open);
        }}
        className={`absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest transition-all ${
          menuOpen ? "opacity-100 bg-surface-container-highest" : "opacity-0 group-hover/item:opacity-100"
        }`}
      >
        <MoreHorizontal size={16} />
      </button>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 4 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className="absolute right-0 top-full mt-1 w-36 glass-gradient-panel border border-outline-variant/40 rounded-xl shadow-md z-[70] overflow-hidden py-1"
          >
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                onShare();
              }}
              className="w-full flex items-center gap-2.5 px-2.5 py-2 text-sm text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors text-left border-0 bg-transparent cursor-pointer"
            >
              <Share2 size={15} strokeWidth={1.75} />
              Share
            </button>
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                onDelete();
              }}
              className="w-full flex items-center gap-2.5 px-2.5 py-2 text-sm text-error hover:bg-error/10 transition-colors text-left border-0 bg-transparent cursor-pointer"
            >
              <Trash2 size={15} strokeWidth={1.75} />
              Delete
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
