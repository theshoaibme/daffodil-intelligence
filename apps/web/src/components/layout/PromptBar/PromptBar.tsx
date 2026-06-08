import React from "react";
import { motion } from "framer-motion";
import { PlusMenuDropdown } from "./PlusMenuDropdown";
import { ModelSelector } from "./ModelSelector";
import { FileAttachmentButton, SendButton, LiveVoiceButton } from "./ActionButtons";
import { BOTTOM_BAR_LAYOUT_ID, enterOrSkip, modeSpring } from "../../../lib/motion";
import { useLocalStorageState } from "../../../hooks/useLocalStorageState";

interface PromptBarProps {
  prompt: string;
  setPrompt: (val: string) => void;
  isSent: boolean;
  handleSend: () => void;
  plusMenuOpen: boolean;
  setPlusMenuOpen: (open: boolean) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  isLoading?: boolean;
  onCopycatMode?: () => void;
  copycatActive?: boolean;
  uiReady?: boolean;
}

export function PromptBar({
  prompt,
  setPrompt,
  handleSend,
  plusMenuOpen,
  setPlusMenuOpen,
  textareaRef,
  isLoading = false,
  onCopycatMode,
  copycatActive = false,
  uiReady = true,
}: PromptBarProps) {
  const [selectedModelId, setSelectedModelId] = useLocalStorageState(
    "di-dashboard-selected-model",
    "gemini-2.0-flash"
  );
  const [selectedTools, setSelectedTools] = useLocalStorageState<string[]>(
    "di-dashboard-selected-tools",
    ["Agent", "Task"]
  );

  const handleToggleTool = (tool: string) => {
    setSelectedTools(prev => 
      prev.includes(tool)
        ? prev.filter(t => t !== tool)
        : [...prev, tool]
    );
  };

  return (
    <div className="fixed bottom-6 left-0 right-0 z-30 flex justify-center w-full px-4 pointer-events-none">
      <motion.div
        layoutId={BOTTOM_BAR_LAYOUT_ID}
        initial={enterOrSkip(uiReady, { opacity: 0, y: 14, scale: 0.96 })}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.94 }}
        transition={modeSpring}
        className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 flex flex-col gap-1 rounded-3xl px-2.5 py-2 relative shadow-md pointer-events-auto"
      >
        <textarea 
          ref={textareaRef}
          rows={1}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="What would you like to change or create?"
          className="w-full bg-transparent border-none outline-none resize-none text-base text-on-surface placeholder-on-surface-variant focus:ring-0 px-1.5 py-1 leading-relaxed max-h-[200px]"
        />

        <div className="flex items-center justify-between px-0.5">
          <div className="flex items-center gap-0.5">
            <PlusMenuDropdown 
              isOpen={plusMenuOpen} 
              setIsOpen={setPlusMenuOpen} 
              selectedTools={selectedTools}
              onToggleTool={handleToggleTool}
              onCopycatMode={onCopycatMode}
              copycatActive={copycatActive}
            />
            <FileAttachmentButton />
          </div>

          <div className="flex items-center gap-2">
            <ModelSelector 
              selectedModelId={selectedModelId}
              onChange={setSelectedModelId}
            />
            <LiveVoiceButton />
            <SendButton onClick={handleSend} disabled={!prompt.trim() || isLoading} loading={isLoading} />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
