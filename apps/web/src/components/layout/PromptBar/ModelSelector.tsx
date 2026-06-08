import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../../lib/routes";
import { motion, AnimatePresence } from "framer-motion";
import { DEFAULT_MODELS, getModels, type ModelInfo } from "../../../lib/models";

export type { ModelInfo };
export { DEFAULT_MODELS, getModels };

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
  const currentModel = models.find((m) => m.id === selectedModelId) || models[0];

  const grouped = models.reduce(
    (acc, model) => {
      if (!acc[model.provider]) acc[model.provider] = [];
      acc[model.provider].push(model);
      return acc;
    },
    {} as Record<string, ModelInfo[]>
  );

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
            <div className="max-h-72 overflow-y-auto custom-scrollbar space-y-2 pr-1">
              {Object.entries(grouped).map(([provider, providerModels]) => (
                <div key={provider}>
                  <p className="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant/60">
                    {provider}
                  </p>
                  <div className="space-y-0.5">
                    {providerModels.map((model) => (
                      <button
                        key={model.id}
                        onClick={() => {
                          onChange(model.id);
                          setIsOpen(false);
                        }}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-surface-container-highest transition-colors text-on-surface text-left cursor-pointer border-0 outline-none"
                      >
                        <span className="text-xs font-medium">{model.name}</span>
                        {selectedModelId === model.id && (
                          <Check size={14} className="text-primary shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-outline-variant/20 my-1 pt-1">
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate(ROUTES.model);
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
