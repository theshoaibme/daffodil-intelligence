import React from "react";
import { motion } from "framer-motion";
import { PlusMenuDropdown } from "./PlusMenuDropdown";
import { GeminiSelector, ModelSelector } from "./ModelSelector";
import { ImageAttachmentButton, SparklesButton, SendButton } from "./ActionButtons";

interface PromptBarProps {
  prompt: string;
  setPrompt: (val: string) => void;
  isSent: boolean;
  handleSend: () => void;
  plusMenuOpen: boolean;
  setPlusMenuOpen: (open: boolean) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
}

export function PromptBar({
  prompt,
  setPrompt,
  handleSend,
  plusMenuOpen,
  setPlusMenuOpen,
  textareaRef
}: PromptBarProps) {
  return (
    <motion.div 
      layout
      className="fixed bottom-6 left-0 right-0 transition-all z-30 transform flex justify-center w-full px-4 pointer-events-none"
    >
      <div className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 flex flex-col gap-2 rounded-3xl p-3 relative shadow-md pointer-events-auto">
        <textarea 
          ref={textareaRef}
          rows={1}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="What would you like to change or create?"
          className="w-full bg-transparent border-none outline-none resize-none text-base text-on-surface placeholder-on-surface-variant focus:ring-0 p-2 leading-relaxed max-h-[200px]"
        />

        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-1">
            <PlusMenuDropdown isOpen={plusMenuOpen} setIsOpen={setPlusMenuOpen} />
            <ImageAttachmentButton />
          </div>

          <div className="flex items-center gap-2">
            <GeminiSelector />
            <ModelSelector modelName="3 Flash" />
            <SparklesButton />
            <SendButton onClick={handleSend} disabled={!prompt.trim()} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
