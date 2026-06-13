import { memo, type ReactNode } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Brain } from "lucide-react";
import {
  RiBrainFill,
  RiChat3Fill,
  RiDatabase2Fill,
  RiQuestionAnswerFill,
  RiTelegramFill,
} from "react-icons/ri";
import { getAgentIconStyle } from "./agentIcons";
import { ICON_SIZE, ROOT_CARD_HEIGHT, ROOT_CARD_WIDTH, ROOT_HUB_Y, rootOutputHandleY } from "./flowLayout";
import {
  getCategoryTheme,
  getIntegrationTheme,
  DEFAULT_NODE_THEME,
  MEMORY_NODE_THEME,
  MODEL_NODE_THEME,
  NODE_RING_OFFSET,
  RESPONSE_NODE_THEME,
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
  targetLeft,
  targetTop,
  children,
}: {
  label: ReactNode;
  theme: { text: string };
  sourceRight?: boolean;
  targetLeft?: boolean;
  targetTop?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="relative" style={{ width: ICON_SIZE, height: ICON_SIZE }}>
      {targetTop && (
        <Handle type="target" position={Position.Top} className="handle-muted" style={{ left: "50%" }} />
      )}
      {targetLeft && (
        <Handle
          type="target"
          position={Position.Left}
          className="handle-muted"
          style={{ top: "50%" }}
        />
      )}
      {sourceRight && (
        <Handle type="source" position={Position.Right} className="handle-primary" style={{ top: "50%" }} />
      )}
      {children}
      <NodeLabel themeText={theme.text}>{label}</NodeLabel>
    </div>
  );
}

function ModelNode({ data }: NodeProps) {
  const theme = MODEL_NODE_THEME;
  const working = Boolean(data.working);

  return (
    <div className="relative" style={{ width: ICON_SIZE, height: ICON_SIZE }}>
      <Handle
        type="source"
        position={Position.Bottom}
        className="handle-primary"
        style={{ left: "50%" }}
      />
      <div
        className={`flex h-full w-full items-center justify-center rounded-full border-2 shadow-sm ${theme.iconBg} ${theme.border} ${
          working ? `ring-2 ring-primary ring-offset-2 ${NODE_RING_OFFSET}` : ""
        }`}
      >
        <RiBrainFill size={26} className="text-primary" />
      </div>
      <NodeLabel themeText={theme.text}>{data.label as string}</NodeLabel>
    </div>
  );
}

function RootNode({ data }: NodeProps) {
  const inputs = (data.inputs as string[] | undefined) ?? [];
  const modelInputs = (data.modelInputs as string[] | undefined) ?? [];
  const outputHandle = data.outputHandle as string | undefined;
  const sideOutputs = (data.sideOutputs as string[] | undefined) ?? [];
  const outputs = (data.outputs as string[] | undefined) ?? [];
  const theme = ROOT_NODE_THEME;
  const sideOutputCount = sideOutputs.length || 2;

  return (
    <div
      className={`root-node-shell relative rounded-sm px-4 py-2 text-center shadow-md backdrop-blur-sm ${theme.bg} ${
        data.working ? `ring-2 ring-primary/40 ${NODE_RING_OFFSET}` : ""
      }`}
      style={{ minWidth: ROOT_CARD_WIDTH, minHeight: ROOT_CARD_HEIGHT }}
    >
      {modelInputs.map((inputId, index) => {
        const left = ((index + 0.5) / modelInputs.length) * 100;
        return (
          <Handle
            key={inputId}
            id={inputId}
            type="target"
            position={Position.Top}
            className="handle-primary"
            style={{ left: `${left}%` }}
          />
        );
      })}

      {inputs.map((inputId) => (
        <Handle
          key={inputId}
          id={inputId}
          type="target"
          position={Position.Left}
          className="handle-primary"
          style={{ top: ROOT_HUB_Y }}
        />
      ))}

      {sideOutputs.length > 0
        ? sideOutputs.map((handleId, index) => (
            <Handle
              key={handleId}
              id={handleId}
              type="source"
              position={Position.Right}
              className="handle-primary"
              style={{ top: rootOutputHandleY(index, sideOutputCount) }}
            />
          ))
        : outputHandle && (
            <Handle
              id={outputHandle}
              type="source"
              position={Position.Right}
              className="handle-primary"
              style={{ top: ROOT_HUB_Y }}
            />
          )}

      <div className="mx-auto flex flex-col items-center" style={{ width: ICON_SIZE }}>
        <div
          className={`root-node-icon flex items-center justify-center rounded-full shadow-sm ${theme.iconBg}`}
          style={{ width: ICON_SIZE, height: ICON_SIZE }}
        >
          <Brain size={28} className="text-primary" />
        </div>
        <p className={`mt-1.5 text-xs font-medium leading-tight whitespace-nowrap ${theme.text}`}>
          {data.label as string}
        </p>
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

function ResponseOutputNode({ data }: NodeProps) {
  const working = Boolean(data.working);
  const theme = RESPONSE_NODE_THEME;
  const surface = DEFAULT_NODE_THEME;

  return (
    <IconNodeFrame label={data.label as string} theme={theme} targetLeft>
      <div
        className={`flex h-full w-full items-center justify-center rounded-full border-2 shadow-sm ${surface.iconBg} ${surface.border} ${
          working ? `ring-2 ring-emerald-500 ring-offset-2 ${NODE_RING_OFFSET}` : ""
        }`}
      >
        <RiQuestionAnswerFill size={26} className="text-emerald-600" />
      </div>
    </IconNodeFrame>
  );
}

function MemoryOutputNode({ data }: NodeProps) {
  const working = Boolean(data.working);
  const theme = MEMORY_NODE_THEME;
  const surface = DEFAULT_NODE_THEME;

  return (
    <IconNodeFrame label={data.label as string} theme={theme} targetLeft>
      <div
        className={`flex h-full w-full items-center justify-center rounded-full border-2 shadow-sm ${surface.iconBg} ${surface.border} ${
          working ? `ring-2 ring-violet-500 ring-offset-2 ${NODE_RING_OFFSET}` : ""
        }`}
      >
        <RiDatabase2Fill size={26} className="text-violet-600" />
      </div>
    </IconNodeFrame>
  );
}

function IntegrationInputNode({ data }: NodeProps) {
  const integration = (data.integration as keyof typeof integrationIcons) || "chat";
  const iconStyle = integrationIcons[integration] ?? integrationIcons.chat;
  const theme = getIntegrationTheme(integration);
  const surface = DEFAULT_NODE_THEME;
  const Icon = iconStyle.icon;
  const working = Boolean(data.working);

  return (
    <IconNodeFrame label={data.label as string} theme={theme} sourceRight>
      <div
        className={`flex h-full w-full items-center justify-center rounded-full border-2 shadow-sm ${surface.iconBg} ${surface.border} ${
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
  const surface = DEFAULT_NODE_THEME;
  const { icon: Icon, iconColor } = getAgentIconStyle(id, category);
  const working = Boolean(data.working);

  return (
    <IconNodeFrame label={data.label as string} theme={theme} targetTop>
      <div
        className={`flex h-full w-full cursor-default items-center justify-center rounded-full border-2 shadow-sm transition-shadow ${surface.iconBg} ${surface.border} ${
          selected
            ? `ring-2 ring-primary/40 ${NODE_RING_OFFSET}`
            : ""
        } ${working && !selected ? `ring-2 ring-primary ring-offset-2 ${NODE_RING_OFFSET}` : ""}`}
      >
        <Icon size={28} className={iconColor} />
      </div>
    </IconNodeFrame>
  );
}

export const flowNodeTypes = {
  root: memo(RootNode),
  model: memo(ModelNode),
  integration: memo(IntegrationInputNode),
  response: memo(ResponseOutputNode),
  memory: memo(MemoryOutputNode),
  category: memo(CategoryNode),
  agent: memo(AgentNode),
};
