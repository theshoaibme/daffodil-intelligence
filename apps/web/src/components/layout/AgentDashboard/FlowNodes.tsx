import { memo, type ReactNode } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Brain } from "lucide-react";
import { RiChat3Fill, RiTelegramFill } from "react-icons/ri";
import { getAgentIconStyle } from "./agentIcons";
import { ICON_SIZE, ROOT_ICON_CENTER } from "./flowLayout";

const categoryColors: Record<string, string> = {
  university: "text-secondary bg-secondary-container/50 border-secondary/30",
  computer: "text-primary bg-primary/10 border-primary/30",
  orchestration: "text-tertiary bg-tertiary/10 border-tertiary/30",
  productivity: "text-green-600 bg-green-50 border-green-200",
  ai: "text-purple-600 bg-purple-50 border-purple-200",
  general: "text-on-surface-variant bg-surface-container border-outline-variant",
};

const integrationIcons = {
  telegram: { icon: RiTelegramFill, color: "text-sky-500" },
  chat: { icon: RiChat3Fill, color: "text-indigo-500" },
} as const;

function NodeLabel({ children }: { children: ReactNode }) {
  return (
    <span
      className="pointer-events-none absolute left-1/2 z-10 mt-1.5 w-24 -translate-x-1/2 text-center text-xs font-medium leading-tight text-on-surface"
      style={{ top: ICON_SIZE }}
    >
      {children}
    </span>
  );
}

function IconNodeFrame({
  label,
  sourceRight,
  targetTop,
  children,
}: {
  label: ReactNode;
  sourceRight?: boolean;
  targetTop?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="relative" style={{ width: ICON_SIZE, height: ICON_SIZE }}>
      {targetTop && <Handle type="target" position={Position.Top} className="handle-muted" />}
      {sourceRight && <Handle type="source" position={Position.Right} />}
      {children}
      <NodeLabel>{label}</NodeLabel>
    </div>
  );
}

function RootNode({ data }: NodeProps) {
  const inputs = (data.inputs as string[] | undefined) ?? [];
  const outputs = (data.outputs as string[] | undefined) ?? [];

  return (
    <div
      className={`relative min-w-[200px] rounded-2xl border-2 border-primary bg-surface-container-lowest px-5 pb-4 pt-4 text-center shadow-md ${
        data.working ? "ring-2 ring-primary/40 ring-offset-2 ring-offset-[#f4f2ff]" : ""
      }`}
    >
      {inputs.map((inputId) => (
        <Handle
          key={inputId}
          id={inputId}
          type="target"
          position={Position.Left}
          style={{ top: ROOT_ICON_CENTER }}
        />
      ))}

      <div className="mx-auto flex flex-col items-center" style={{ width: ICON_SIZE }}>
        <div
          className="flex items-center justify-center rounded-full bg-primary/15"
          style={{ width: ICON_SIZE, height: ICON_SIZE }}
        >
          <Brain size={28} className="text-primary" />
        </div>
        <p className="mt-2 text-sm font-semibold text-on-surface">{data.label as string}</p>
      </div>

      {outputs.map((outputId, index) => {
        const left = ((index + 0.5) / outputs.length) * 100;
        return (
          <Handle
            key={outputId}
            id={outputId}
            type="source"
            position={Position.Bottom}
            style={{ left: `${left}%` }}
          />
        );
      })}
    </div>
  );
}

function IntegrationInputNode({ data }: NodeProps) {
  const integration = (data.integration as keyof typeof integrationIcons) || "chat";
  const style = integrationIcons[integration] ?? integrationIcons.chat;
  const Icon = style.icon;

  return (
    <IconNodeFrame label={data.label as string} sourceRight>
      <div className="flex h-full w-full items-center justify-center rounded-full border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
        <Icon size={28} className={style.color} />
      </div>
    </IconNodeFrame>
  );
}

function CategoryNode({ data }: NodeProps) {
  const category = (data.category as string) || "general";
  const catColor = categoryColors[category] || categoryColors.general;

  return (
    <div
      className={`relative min-w-[88px] rounded-xl border-2 bg-surface-container-lowest px-3 py-2 shadow-sm ${catColor}`}
    >
      <Handle type="target" position={Position.Top} className="handle-muted" />
      <Handle type="source" position={Position.Bottom} className="handle-muted" />
      <span className="block text-center text-[10px] font-bold leading-tight">{data.label as string}</span>
    </div>
  );
}

function AgentNode({ data, id, selected }: NodeProps) {
  const category = (data.category as string) || "general";
  const { icon: Icon, iconColor } = getAgentIconStyle(id, category);
  const working = Boolean(data.working);

  return (
    <IconNodeFrame label={data.label as string} targetTop>
      <div
        className={`flex h-full w-full cursor-pointer items-center justify-center rounded-full border bg-surface-container-lowest shadow-sm transition-shadow ${
          selected
            ? "border-primary ring-2 ring-primary/40 ring-offset-2 ring-offset-[#f4f2ff]"
            : "border-outline-variant/50"
        } ${working && !selected ? "ring-2 ring-primary ring-offset-2 ring-offset-[#f4f2ff]" : ""}`}
      >
        <Icon size={28} className={iconColor} />
      </div>
    </IconNodeFrame>
  );
}

export const flowNodeTypes = {
  root: memo(RootNode),
  integration: memo(IntegrationInputNode),
  category: memo(CategoryNode),
  agent: memo(AgentNode),
};
