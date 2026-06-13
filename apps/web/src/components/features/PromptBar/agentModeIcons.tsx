import type { ReactNode } from "react";
import { Brain, Cat, Infinity, Telescope } from "lucide-react";
import type { AgentMode } from "@lib";

const ICON_SIZE = 14;
const ICON_STROKE = 1.75;

/** MCP-style connected nodes icon (matches MCP server tooling). */
export function McpIcon({ size = ICON_SIZE }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={ICON_STROKE}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="6" r="2.5" />
      <circle cx="12" cy="18" r="2.5" />
      <path d="M8.2 7.4 10.8 15.2" />
      <path d="M15.8 7.4 13.2 15.2" />
      <path d="M8.5 6h7" />
    </svg>
  );
}

function iconProps(size = ICON_SIZE) {
  return { size, strokeWidth: ICON_STROKE };
}

export const AGENT_MODE_ICONS: Record<AgentMode, ReactNode> = {
  MCP: <McpIcon />,
  Agent: <Infinity {...iconProps()} />,
  Research: <Telescope {...iconProps()} />,
  Planning: <Brain {...iconProps()} />,
};

export const COPYCAT_MODE_ICON = <Cat {...iconProps()} />;
