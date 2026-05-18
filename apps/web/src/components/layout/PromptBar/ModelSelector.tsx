import { ChevronDown } from "lucide-react";

export function GeminiSelector() {
  return (
    <div className="flex items-center gap-1.5 bg-surface-container-highest/60 hover:bg-surface-container-highest px-3 py-1.5 border border-outline-variant/20 cursor-pointer transition-colors rounded-full lg:flex hidden select-none">
      <div className="w-5 h-5 rounded-full bg-primary border border-black/20"></div>
      <span className="text-xs font-medium text-on-surface-variant">Gemini</span>
      <ChevronDown size={14} className="text-on-surface-variant" />
    </div>
  );
}

interface ModelSelectorProps {
  modelName: string;
}

export function ModelSelector({ modelName }: ModelSelectorProps) {
  return (
    <button className="flex items-center gap-2 bg-surface-container-highest/60 hover:bg-surface-container-highest px-4 py-2 text-on-surface transition-colors border border-outline-variant/20 rounded-full cursor-pointer outline-none">
      <span className="text-xs font-medium">{modelName}</span>
      <ChevronDown size={14} />
    </button>
  );
}
