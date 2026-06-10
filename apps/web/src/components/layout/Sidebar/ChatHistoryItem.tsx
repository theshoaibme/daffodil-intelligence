import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";
import { createPortal } from "react-dom";
import { MessageSquare, MoreHorizontal, Trash2, Share2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { formatHistoryDate } from "@lib";
import { dropdownPanelVariants } from "@lib";
import { DropdownItem } from "@ui";

interface ChatHistoryItemProps {
  id: string;
  title: string;
  updatedAt: string;
  active?: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onShare: () => void;
}

const MENU_WIDTH = 144;
const MENU_HEIGHT = 88;

function useChatMenuPosition(open: boolean, anchorRef: RefObject<HTMLButtonElement | null>) {
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  useLayoutEffect(() => {
    if (!open || !anchorRef.current) {
      setPosition(null);
      return;
    }

    const update = () => {
      const rect = anchorRef.current?.getBoundingClientRect();
      if (!rect) return;

      const spaceBelow = window.innerHeight - rect.bottom;
      const openUp = spaceBelow < MENU_HEIGHT + 8;
      const top = openUp ? rect.top - MENU_HEIGHT - 6 : rect.bottom + 6;
      const left = Math.min(
        Math.max(8, rect.right - MENU_WIDTH),
        window.innerWidth - MENU_WIDTH - 8
      );

      setPosition({ top, left });
    };

    update();
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [open, anchorRef]);

  return position;
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
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuPosition = useChatMenuPosition(menuOpen, menuButtonRef);

  useEffect(() => {
    if (!menuOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (containerRef.current?.contains(target)) return;
      if (menuButtonRef.current?.contains(target)) return;
      if (menuRef.current?.contains(target)) return;
      setMenuOpen(false);
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  const menu = (
    <AnimatePresence>
      {menuOpen && menuPosition && (
        <motion.div
          ref={menuRef}
          role="menu"
          variants={dropdownPanelVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          style={{
            top: menuPosition.top,
            left: menuPosition.left,
            width: MENU_WIDTH,
            transformOrigin: "top right",
          }}
          className="fixed z-[200] glass-gradient-panel border border-outline-variant/40 rounded-2xl shadow-md overflow-hidden p-1"
        >
          <DropdownItem
            icon={<Share2 size={15} strokeWidth={1.75} />}
            text="Share"
            onClick={() => {
              setMenuOpen(false);
              onShare();
            }}
          />
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setMenuOpen(false);
              onDelete();
            }}
            className="w-full flex items-center gap-2.5 pl-2.5 pr-2 py-1.5 rounded-lg text-sm text-error hover:bg-error/10 transition-colors text-left border-0 bg-transparent cursor-pointer"
          >
            <Trash2 size={15} strokeWidth={1.75} />
            Delete
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      <div ref={containerRef} className="relative group/item">
        <button
          type="button"
          onClick={onSelect}
          className={`flex items-center gap-2 px-2 py-0.5 pr-8 rounded-lg cursor-pointer transition-all text-left w-full border-0 min-h-[28px] ${
            active
              ? "bg-surface-container-highest text-on-surface"
              : "bg-transparent text-on-surface hover:bg-surface-container-high"
          }`}
        >
          <div className="w-6 h-6 rounded-md bg-surface-container-highest flex items-center justify-center border border-outline-variant/10 shrink-0">
            <MessageSquare size={12} className="text-on-surface-variant" strokeWidth={1.75} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs truncate leading-4">
              <span className="font-medium text-on-surface">{title}</span>
              <span className="text-on-surface-variant"> · {formatHistoryDate(updatedAt)}</span>
            </p>
          </div>
        </button>

        <button
          ref={menuButtonRef}
          type="button"
          aria-label="Chat options"
          aria-expanded={menuOpen}
          aria-haspopup="menu"
          onClick={(event) => {
            event.stopPropagation();
            setMenuOpen((open) => !open);
          }}
          className={`absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest transition-all border-0 cursor-pointer ${
            menuOpen ? "opacity-100 bg-surface-container-highest" : "opacity-0 group-hover/item:opacity-100"
          }`}
        >
          <MoreHorizontal size={14} />
        </button>
      </div>

      {typeof document !== "undefined" ? createPortal(menu, document.body) : null}
    </>
  );
}
