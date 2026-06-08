import { memo, type ElementType } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Bot, Brain, Cpu, Monitor, Zap } from "lucide-react";

const categoryColors: Record<string, string> = {
  university: "text-secondary bg-secondary-container/50 border-secondary/30",
  computer: "text-primary bg-primary/10 border-primary/30",
  orchestration: "text-tertiary bg-tertiary/10 border-tertiary/30",
  productivity: "text-green-600 bg-green-50 border-green-200",
  ai: "text-purple-600 bg-purple-50 border-purple-200",
  general: "text-on-surface-variant bg-surface-container border-outline-variant",
};

const categoryIcons: Record<string, ElementType> = {
  university: Bot,
  computer: Monitor,
  orchestration: Brain,
  productivity: Zap,
  ai: Cpu,
  general: Bot,
};

const statusDots: Record<string, string> = {
  idle: "bg-outline-variant",
  thinking: "bg-primary animate-pulse",
  executing: "bg-tertiary animate-pulse",
  error: "bg-error",
};

function RootNode({ data }: NodeProps) {
  return (
    <div
      className={`relative px-5 py-4 min-w-[200px] rounded-2xl border-2 border-primary bg-surface-container-lowest shadow-md text-center ${
        data.working ? "ring-2 ring-primary/40 ring-offset-2 ring-offset-[#f4f2ff]" : ""
      }`}
    >
      <Handle type="source" position={Position.Bottom} className="!bg-primary !w-2 !h-2 !border-0" />
      <div className="w-14 h-14 mx-auto rounded-full bg-primary/15 flex items-center justify-center mb-2">
        <Brain size={28} className="text-primary" />
      </div>
      <p className="text-sm font-semibold text-on-surface">{data.label as string}</p>
    </div>
  );
}

function CategoryNode({ data }: NodeProps) {
  const category = (data.category as string) || "general";
  const catColor = categoryColors[category] || categoryColors.general;
  const Icon = categoryIcons[category] || Bot;

  return (
    <div className={`relative flex items-center gap-2 px-4 py-2 rounded-xl border-2 bg-surface-container-lowest shadow-sm ${catColor}`}>
      <Handle type="target" position={Position.Top} className="!bg-outline-variant !w-2 !h-2 !border-0" />
      <Handle type="source" position={Position.Bottom} className="!bg-outline-variant !w-2 !h-2 !border-0" />
      <Icon size={16} />
      <span className="text-xs font-bold uppercase tracking-wider">{data.label as string}</span>
    </div>
  );
}

function AgentNode({ data }: NodeProps) {
  const category = (data.category as string) || "general";
  const catColor = categoryColors[category] || categoryColors.general;
  const Icon = categoryIcons[category] || Bot;
  const status = (data.status as string) || "idle";
  const working = Boolean(data.working);

  return (
    <div
      className={`relative w-44 p-3 rounded-2xl border-2 bg-surface-container-lowest shadow-sm transition-shadow ${
        working
          ? "border-primary shadow-md ring-2 ring-primary/30"
          : "border-outline-variant hover:border-primary/40"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-outline-variant !w-2 !h-2 !border-0" />
      <div className={`w-11 h-11 mx-auto rounded-full flex items-center justify-center mb-2 ${catColor}`}>
        <Icon size={22} />
      </div>
      <p className="text-sm font-semibold text-on-surface text-center leading-snug line-clamp-2">
        {data.label as string}
      </p>
      <span className={`mt-1.5 block text-center text-[10px] font-medium px-2 py-0.5 rounded-full capitalize mx-auto w-fit ${catColor}`}>
        {category}
      </span>
      <div className="absolute -top-1 -right-1 flex items-center bg-surface-container-lowest border border-outline-variant rounded-full px-1.5 py-0.5 shadow-sm">
        <div className={`w-2 h-2 rounded-full ${statusDots[status] || statusDots.idle}`} />
      </div>
    </div>
  );
}

export const flowNodeTypes = {
  root: memo(RootNode),
  category: memo(CategoryNode),
  agent: memo(AgentNode),
};
