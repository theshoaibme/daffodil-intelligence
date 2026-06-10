import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Send, X, CornerDownLeft, ArrowBigUp, Delete } from "lucide-react";
import { modeSpring } from "@lib";

interface KeyboardInputProps {
  onSendText: (text: string) => void;
  onSendHotkey: (keys: string[]) => void;
  onClose: () => void;
}

const QUICK_KEYS: { label: string; keys: string[]; icon?: React.ReactNode }[] = [
  { label: "Enter", keys: ["enter"], icon: <CornerDownLeft size={12} /> },
  { label: "Escape", keys: ["escape"] },
  { label: "Tab", keys: ["tab"] },
  { label: "Backspace", keys: ["backspace"], icon: <Delete size={12} /> },
  { label: "Ctrl+Z", keys: ["ctrl", "z"] },
  { label: "Ctrl+C", keys: ["ctrl", "c"] },
  { label: "Ctrl+V", keys: ["ctrl", "v"] },
  { label: "Ctrl+A", keys: ["ctrl", "a"] },
  { label: "Ctrl+S", keys: ["ctrl", "s"] },
  { label: "Alt+F4", keys: ["alt", "f4"] },
];

export function KeyboardInput({
  onSendText,
  onSendHotkey,
  onClose,
}: KeyboardInputProps) {
  const [typeText, setTypeText] = useState("");
  const [recentTexts, setRecentTexts] = useState<string[]>([]);
  const [showHotkeys, setShowHotkeys] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const sendText = useCallback(() => {
    if (!typeText.trim()) return;
    onSendText(typeText);
    setRecentTexts((prev) => [typeText, ...prev.filter((t) => t !== typeText)].slice(0, 5));
    setTypeText("");
    inputRef.current?.focus();
  }, [typeText, onSendText]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.96 }}
      transition={modeSpring}
      className="fixed bottom-20 left-0 right-0 z-50 flex justify-center w-full px-4 pointer-events-none"
    >
      <div className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 rounded-3xl p-3 shadow-md pointer-events-auto">
        {/* Mode toggle */}
        <div className="flex items-center gap-1 mb-2">
          <button
            type="button"
            onClick={() => setShowHotkeys(false)}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              !showHotkeys
                ? "bg-primary text-on-primary"
                : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
            }`}
          >
            Type Text
          </button>
          <button
            type="button"
            onClick={() => setShowHotkeys(true)}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              showHotkeys
                ? "bg-primary text-on-primary"
                : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
            }`}
          >
            <ArrowBigUp size={12} className="inline mr-0.5" />
            Hotkeys
          </button>
          <button
            type="button"
            onClick={onClose}
            className="ml-auto p-1 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
            aria-label="Close keyboard"
          >
            <X size={14} />
          </button>
        </div>

        {!showHotkeys ? (
          <>
            {/* Text input row */}
            <div className="flex gap-2">
              <input
                ref={inputRef}
                value={typeText}
                onChange={(e) => setTypeText(e.target.value)}
                placeholder="Type text to send…"
                autoFocus
                className="flex-1 px-3 py-2 text-sm rounded-xl bg-surface-container-highest focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-on-surface-variant/50 border-0"
                onKeyDown={(e) => {
                  if (e.key === "Enter") sendText();
                  if (e.key === "Escape") onClose();
                }}
              />
              <button
                type="button"
                onClick={sendText}
                disabled={!typeText.trim()}
                aria-label="Send text"
                className="w-10 h-10 flex items-center justify-center rounded-xl bg-primary text-on-primary disabled:opacity-50 transition-opacity"
              >
                <Send size={16} />
              </button>
            </div>

            {/* Recent texts */}
            {recentTexts.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {recentTexts.map((text) => (
                  <button
                    key={text}
                    type="button"
                    onClick={() => {
                      setTypeText(text);
                      inputRef.current?.focus();
                    }}
                    className="px-2 py-0.5 text-[10px] font-medium text-on-surface-variant bg-surface-container-high rounded-full hover:bg-surface-container-highest truncate max-w-[120px]"
                  >
                    {text}
                  </button>
                ))}
              </div>
            )}
          </>
        ) : (
          /* Hotkey grid */
          <div className="grid grid-cols-5 gap-1.5">
            {QUICK_KEYS.map((hk) => (
              <button
                key={hk.label}
                type="button"
                onClick={() => onSendHotkey(hk.keys)}
                className="flex items-center justify-center gap-1 px-2 py-2 text-xs font-medium rounded-xl bg-surface-container-high text-on-surface hover:bg-surface-container-highest transition-colors active:scale-95"
              >
                {hk.icon}
                {hk.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
