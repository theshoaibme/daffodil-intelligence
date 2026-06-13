export const AGENT_MODES = ["MCP", "Agent", "Research", "Planning"] as const;

export type AgentMode = (typeof AGENT_MODES)[number];

export const DEFAULT_AGENT_MODE: AgentMode = "Agent";

export const AGENT_MODE_PLACEHOLDERS: Record<AgentMode, string> = {
  MCP: "What would you like to do with MCP tools?",
  Agent: "What would you like the agent to do?",
  Research: "What should I research?",
  Planning: "What would you like to plan?",
};

export function normalizeAgentMode(value: unknown): AgentMode {
  if (typeof value === "string" && AGENT_MODES.includes(value as AgentMode)) {
    return value as AgentMode;
  }
  if (Array.isArray(value) && value.length > 0) {
    const first = value.find(
      (item) => typeof item === "string" && AGENT_MODES.includes(item as AgentMode)
    );
    if (typeof first === "string") return first as AgentMode;
  }
  return DEFAULT_AGENT_MODE;
}
