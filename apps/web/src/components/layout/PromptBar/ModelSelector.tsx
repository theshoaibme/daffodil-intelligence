import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  isCustom?: boolean;
  apiUrl?: string;
  apiKey?: string;
}

export const DEFAULT_MODELS: ModelInfo[] = [
  { id: "gemini-3-flash", name: "Gemini 3 Flash", provider: "Gemini" },
  { id: "gemini-3-pro", name: "Gemini 3 Pro", provider: "Gemini" },
  { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash", provider: "Gemini" },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Gemini" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "gpt-4o-mini", name: "GPT-4o mini", provider: "OpenAI" },
  { id: "gpt-4", name: "GPT-4", provider: "OpenAI" },
  { id: "claude-3.5-sonnet", name: "Claude 3.5 Sonnet", provider: "Claude" },
  { id: "claude-3.5-haiku", name: "Claude 3.5 Haiku", provider: "Claude" },
  { id: "claude-3-opus", name: "Claude 3 Opus", provider: "Claude" },
];

export function getModels(): ModelInfo[] {
  try {
    const custom = localStorage.getItem("daffodil_custom_models");
    if (custom) {
      const parsed = JSON.parse(custom);
      return [...DEFAULT_MODELS, ...parsed];
    }
  } catch (e) {
    console.error(e);
  }
  return DEFAULT_MODELS;
}

interface ModelSelectorProps {
  selectedModelId: string;
  onChange: (modelId: string) => void;
}

export function ModelSelector({ selectedModelId, onChange }: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const models = getModels();
  const currentModel = models.find(m => m.id === selectedModelId) || models[0];

  return (
    <div className="relative" ref={containerRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-surface-container-highest/60 hover:bg-surface-container-highest px-3 py-1 text-on-surface transition-colors rounded-full cursor-pointer outline-none"
      >
        <span className="text-xs font-medium">{currentModel.name}</span>
        <ChevronDown size={14} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className="absolute bottom-full right-0 mb-2 w-64 bg-surface-container-high border border-outline-variant/40 rounded-2xl shadow-xl z-[60] overflow-hidden p-2"
          >
            <div className="max-h-60 overflow-y-auto custom-scrollbar space-y-1 pr-1">
              {models.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    onChange(model.id);
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-surface-container-highest transition-colors text-on-surface text-left cursor-pointer border-0 outline-none"
                >
                  <div className="flex flex-col">
                    <span className="text-xs font-medium">{model.name}</span>
                    <span className="text-[10px] text-on-surface-variant/70">{model.provider}</span>
                  </div>
                  {selectedModelId === model.id && <Check size={14} className="text-primary" />}
                </button>
              ))}
            </div>

            <div className="border-t border-outline-variant/20 my-1 pt-1">
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate("/model");
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-surface-container-highest transition-colors text-primary text-left cursor-pointer border-0 outline-none font-medium"
              >
                <Plus size={14} />
                <span className="text-xs">Add model</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
