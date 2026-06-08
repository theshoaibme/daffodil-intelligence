import React, { useState } from "react";
import { motion } from "framer-motion";
import { PlusMenuDropdown } from "./PlusMenuDropdown";
import { ModelSelector } from "./ModelSelector";
import { ImageAttachmentButton, SendButton, LiveVoiceButton } from "./ActionButtons";

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
}: PromptBarProps) {
  const [selectedModelId, setSelectedModelId] = useState<string>("gemini-2.0-flash");
  const [selectedTools, setSelectedTools] = useState<string[]>(["Agent", "Task"]);

  const handleToggleTool = (tool: string) => {
    setSelectedTools(prev => 
      prev.includes(tool)
        ? prev.filter(t => t !== tool)
        : [...prev, tool]
    );
  };

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
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="What would you like to change or create?"
          className="w-full bg-transparent border-none outline-none resize-none text-base text-on-surface placeholder-on-surface-variant focus:ring-0 p-2 leading-relaxed max-h-[200px]"
        />

        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-1">
            <PlusMenuDropdown 
              isOpen={plusMenuOpen} 
              setIsOpen={setPlusMenuOpen} 
              selectedTools={selectedTools}
              onToggleTool={handleToggleTool}
              onCopycatMode={onCopycatMode}
              copycatActive={copycatActive}
            />
            <ImageAttachmentButton />
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
      </div>
    </motion.div>
  );
}
