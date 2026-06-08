import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Brain } from "lucide-react";
import { getAgentIconStyle } from "./agentIcons";

const categoryColors: Record<string, string> = {
  university: "text-secondary bg-secondary-container/50 border-secondary/30",
  computer: "text-primary bg-primary/10 border-primary/30",
  orchestration: "text-tertiary bg-tertiary/10 border-tertiary/30",
  productivity: "text-green-600 bg-green-50 border-green-200",
  ai: "text-purple-600 bg-purple-50 border-purple-200",
  general: "text-on-surface-variant bg-surface-container border-outline-variant",
};

function RootNode({ data }: NodeProps) {
  const outputs = (data.outputs as string[] | undefined) ?? [];

  return (
    <div
      className={`relative px-5 py-4 min-w-[200px] rounded-2xl border-2 border-primary bg-surface-container-lowest shadow-md text-center ${
        data.working ? "ring-2 ring-primary/40 ring-offset-2 ring-offset-[#f4f2ff]" : ""
      }`}
    >
      <div className="w-14 h-14 mx-auto rounded-full bg-primary/15 flex items-center justify-center mb-2">
        <Brain size={28} className="text-primary" />
      </div>
      <p className="text-sm font-semibold text-on-surface">{data.label as string}</p>

      {outputs.map((outputId, index) => {
        const left = ((index + 0.5) / outputs.length) * 100;
        return (
          <Handle
            key={outputId}
            id={outputId}
            type="source"
            position={Position.Bottom}
            className="!bg-primary !w-2.5 !h-2.5 !border-2 !border-white"
            style={{ left: `${left}%` }}
          />
        );
      })}
    </div>
  );
}

function CategoryNode({ data }: NodeProps) {
  const category = (data.category as string) || "general";
  const catColor = categoryColors[category] || categoryColors.general;

  return (
    <div className={`relative px-3 py-2 min-w-[88px] rounded-xl border-2 bg-surface-container-lowest shadow-sm ${catColor}`}>
      <Handle type="target" position={Position.Top} className="!bg-outline-variant !w-2 !h-2 !border-0" />
      <Handle type="source" position={Position.Bottom} className="!bg-outline-variant !w-2 !h-2 !border-0" />
      <span className="text-[10px] font-bold text-center leading-tight block">{data.label as string}</span>
    </div>
  );
}

function AgentNode({ data, id }: NodeProps) {
  const category = (data.category as string) || "general";
  const { icon: Icon, iconColor } = getAgentIconStyle(id, category);
  const working = Boolean(data.working);

  return (
    <div className="relative flex flex-col items-center gap-2">
      <Handle type="target" position={Position.Top} className="!bg-outline-variant !w-2 !h-2 !border-0" />
      <div
        className={`w-14 h-14 rounded-full flex items-center justify-center bg-surface-container-lowest border border-outline-variant/50 shadow-sm transition-shadow ${
          working ? "ring-2 ring-primary ring-offset-2 ring-offset-[#f4f2ff]" : ""
        }`}
      >
        <Icon size={28} className={iconColor} />
      </div>
      <p className="text-xs font-medium text-on-surface text-center max-w-[96px] leading-tight line-clamp-2">
        {data.label as string}
      </p>
    </div>
  );
}

export const flowNodeTypes = {
  root: memo(RootNode),
  category: memo(CategoryNode),
  agent: memo(AgentNode),
};
