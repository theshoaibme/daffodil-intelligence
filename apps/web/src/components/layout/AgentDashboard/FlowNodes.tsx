import { memo, type ReactNode } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Brain } from "lucide-react";
import { RiChat3Fill, RiTelegramFill } from "react-icons/ri";
import { getAgentIconStyle } from "./agentIcons";
import { ICON_SIZE, ROOT_ICON_CENTER } from "./flowLayout";
import {
  getCategoryTheme,
  getIntegrationTheme,
  NODE_RING_OFFSET,
  ROOT_NODE_THEME,
} from "./flowNodeTheme";

const integrationIcons = {
  telegram: { icon: RiTelegramFill, color: "text-sky-500" },
  chat: { icon: RiChat3Fill, color: "text-indigo-500" },
} as const;

function NodeLabel({ children, themeText }: { children: ReactNode; themeText: string }) {
  return (
    <span
      className={`pointer-events-none absolute left-1/2 z-10 mt-1.5 w-24 -translate-x-1/2 text-center text-xs font-medium leading-tight ${themeText}`}
      style={{ top: ICON_SIZE }}
    >
      {children}
    </span>
  );
}

function IconNodeFrame({
  label,
  theme,
  sourceRight,
  targetTop,
  children,
}: {
  label: ReactNode;
  theme: { text: string };
  sourceRight?: boolean;
  targetTop?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="relative" style={{ width: ICON_SIZE, height: ICON_SIZE }}>
      {targetTop && <Handle type="target" position={Position.Top} className="handle-muted" />}
      {sourceRight && <Handle type="source" position={Position.Right} />}
      {children}
      <NodeLabel themeText={theme.text}>{label}</NodeLabel>
    </div>
  );
}

function RootNode({ data }: NodeProps) {
  const inputs = (data.inputs as string[] | undefined) ?? [];
  const outputs = (data.outputs as string[] | undefined) ?? [];
  const theme = ROOT_NODE_THEME;

  return (
    <div
      className={`relative min-w-[200px] rounded-2xl border-2 px-5 pb-4 pt-4 text-center shadow-md ${theme.bg} ${theme.border} ${
        data.working ? `ring-2 ring-primary/40 ${NODE_RING_OFFSET}` : ""
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
          className={`flex items-center justify-center rounded-full ${theme.iconBg}`}
          style={{ width: ICON_SIZE, height: ICON_SIZE }}
        >
          <Brain size={28} className="text-primary" />
        </div>
        <p className={`mt-2 text-sm font-semibold ${theme.text}`}>{data.label as string}</p>
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
  const iconStyle = integrationIcons[integration] ?? integrationIcons.chat;
  const theme = getIntegrationTheme(integration);
  const Icon = iconStyle.icon;
  const working = Boolean(data.working);

  return (
    <IconNodeFrame label={data.label as string} theme={theme} sourceRight>
      <div
        className={`flex h-full w-full items-center justify-center rounded-full border shadow-sm ${theme.iconBg} ${theme.border} ${
          working ? `ring-2 ring-primary ring-offset-2 ${NODE_RING_OFFSET}` : ""
        }`}
      >
        <Icon size={28} className={iconStyle.color} />
      </div>
    </IconNodeFrame>
  );
}

function CategoryNode({ data }: NodeProps) {
  const category = (data.category as string) || "general";
  const theme = getCategoryTheme(category);

  return (
    <div
      className={`relative min-w-[88px] rounded-xl border-2 px-3 py-2 shadow-sm ${theme.bg} ${theme.border}`}
    >
      <Handle type="target" position={Position.Top} className="handle-muted" />
      <Handle type="source" position={Position.Bottom} className="handle-muted" />
      <span className={`block text-center text-[10px] font-bold leading-tight ${theme.text}`}>
        {data.label as string}
      </span>
    </div>
  );
}

function AgentNode({ data, id, selected }: NodeProps) {
  const category = (data.category as string) || "general";
  const theme = getCategoryTheme(category);
  const { icon: Icon, iconColor } = getAgentIconStyle(id, category);
  const working = Boolean(data.working);

  return (
    <IconNodeFrame label={data.label as string} theme={theme} targetTop>
      <div
        className={`flex h-full w-full cursor-pointer items-center justify-center rounded-full border shadow-sm transition-shadow ${theme.iconBg} ${
          selected
            ? `border-primary ring-2 ring-primary/40 ${NODE_RING_OFFSET}`
            : theme.border
        } ${working && !selected ? `ring-2 ring-primary ring-offset-2 ${NODE_RING_OFFSET}` : ""}`}
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
