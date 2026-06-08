import { useState, useRef, useEffect } from "react";
import { ChevronDown, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../../lib/routes";
import { motion, AnimatePresence } from "framer-motion";
import { DEFAULT_MODELS, getModels, type ModelInfo } from "../../../lib/models";
import { DropdownItem } from "../../ui";

export type { ModelInfo };
export { DEFAULT_MODELS, getModels };

interface ModelSelectorProps {
  selectedModelId: string;
  onChange: (modelId: string) => void;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="px-2.5 pt-1 pb-1.5 text-[11px] font-medium text-on-surface-variant/70 tracking-wide">
      {children}
    </p>
  );
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
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Select model"
        aria-expanded={isOpen}
        className="flex items-center gap-1.5 bg-surface-container-highest/60 hover:bg-surface-container-highest px-2.5 py-1 text-on-surface-variant hover:text-on-surface transition-colors rounded-full cursor-pointer outline-none border-0"
      >
        <span className="text-xs font-medium">{currentModel.name}</span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className="absolute bottom-full right-0 mb-2 w-56 glass-gradient-panel border border-outline-variant/40 rounded-2xl shadow-md z-[60] overflow-hidden flex flex-col py-1"
          >
            <div className="max-h-72 overflow-y-auto custom-scrollbar px-1 pb-0.5">
              {Object.entries(grouped).map(([provider, providerModels], index) => (
                <div key={provider}>
                  {index > 0 && <div className="mx-1.5 my-1 border-t border-outline-variant/30" />}
                  <SectionLabel>{provider}</SectionLabel>
                  {providerModels.map((model) => (
                    <DropdownItem
                      key={model.id}
                      text={model.name}
                      active={selectedModelId === model.id}
                      onClick={() => {
                        onChange(model.id);
                        setIsOpen(false);
                      }}
                    />
                  ))}
                </div>
              ))}
            </div>

            <div className="mx-2.5 my-1 border-t border-outline-variant/30" />

            <div className="px-1 pt-0.5 pb-1">
              <DropdownItem
                icon={<Plus size={16} strokeWidth={1.75} />}
                text="Add model"
                onClick={() => {
                  setIsOpen(false);
                  navigate(ROUTES.model);
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
