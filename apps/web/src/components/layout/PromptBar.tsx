import React from "react";
import { 
  Plus, 
  ImagePlus, 
  ChevronDown, 
  ArrowUp, 
  Sparkles, 
  Compass, 
  Monitor, 
  CheckCircle2 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { DropdownItem } from "../ui";

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
  isSent,
  handleSend,
  plusMenuOpen,
  setPlusMenuOpen,
  textareaRef
}: PromptBarProps) {
  return (
    <motion.div 
      layout
      className={`fixed transition-all z-50 transform flex justify-center w-full px-4 pointer-events-none ${isSent ? 'bottom-6 left-6 max-w-[480px] justify-start' : 'bottom-6 left-0'}`}
    >
      <div className="w-full max-w-2xl bg-surface-container-high/40 backdrop-blur-xl border border-outline-variant/40 flex flex-col gap-2 rounded-3xl p-3 relative shadow-md pointer-events-auto">
        {/* Plus Menu Popup */}
        <AnimatePresence>
          {plusMenuOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="absolute bottom-full left-3 mb-4 w-56 bg-surface-container-high/95 backdrop-blur-2xl border border-outline-variant/40 rounded-2xl shadow-md z-[60]"
            >
              <div className="p-2 space-y-1">
                <DropdownItem icon={<Compass className="text-primary" size={20} />} text="MCP" />
                <DropdownItem icon={<Monitor className="text-primary" size={20} />} text="Agent" />
                <DropdownItem icon={<Compass className="text-primary" size={20} />} text="Research" />
                <DropdownItem icon={<CheckCircle2 className="text-primary" size={20} />} text="Task" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

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
            <button 
              onClick={() => setPlusMenuOpen(!plusMenuOpen)}
              className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest rounded-full transition-all"
            >
              <Plus size={22} />
            </button>
            <button className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest rounded-full transition-all">
              <ImagePlus size={22} />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 bg-surface-container-highest/60 hover:bg-surface-container-highest px-3 py-1.5 border border-outline-variant/20 cursor-pointer transition-colors rounded-full lg:flex hidden">
              <div className="w-5 h-5 rounded-full bg-primary border border-black/20"></div>
              <span className="text-xs font-medium text-on-surface-variant">Gemini</span>
              <ChevronDown size={14} className="text-on-surface-variant" />
            </div>
            <button className="flex items-center gap-2 bg-surface-container-highest/60 hover:bg-surface-container-highest px-4 py-2 text-on-surface transition-colors border border-outline-variant/20 rounded-full">
              <span className="text-xs font-medium">3 Flash</span>
              <ChevronDown size={14} />
            </button>
            <button className="w-10 h-10 flex items-center justify-center bg-primary/10 text-primary hover:bg-primary/20 rounded-full transition-all">
              <Sparkles size={20} fill="currentColor" />
            </button>
            <button 
              onClick={handleSend}
              className="w-10 h-10 flex items-center justify-center bg-primary text-on-primary rounded-full hover:opacity-90 transition-all font-bold"
            >
              <ArrowUp size={22} strokeWidth={3} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
