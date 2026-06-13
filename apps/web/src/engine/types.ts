export type CardType =
  | "agent"
  | "task"
  | "workflow"
  | "tool"
  | "search"
  | "file"
  | "code"
  | "image"
  | "browser"
  | "result"
  | "approval"
  | "form"
  | "terminal"
  | "chart"
  | "map"
  | "email"
  | "calendar"
  | "database"
  | "block";

export type CardStatus = "pending" | "active" | "success" | "error" | "cancelled";

export interface EventSource {
  agent_id?: string;
  tool_name?: string;
  mcp_server?: string;
  workflow_node_id?: string;
}

export interface AiEventEnvelope {
  v: number;
  id: string;
  seq: number;
  ts: string;
  session_id: string;
  turn_id: string;
  source: EventSource;
  type: string;
  payload: Record<string, unknown>;
  correlation_id?: string;
  parent_event_id?: string;
  legacy_type?: string;
}

export interface Card {
  id: string;
  card_type: CardType;
  status: CardStatus;
  title: string;
  subtitle?: string;
  icon?: string;
  timestamp: string;
  source: EventSource;
  layout: "inline" | "panel" | "fullscreen" | "dock";
  priority: number;
  collapsible: boolean;
  children?: string[];
  payload: Record<string, unknown>;
  turn_id?: string;
  correlation_id?: string;
}

export interface StreamState {
  messageId: string | null;
  content: string;
  thinking: string;
  isStreaming: boolean;
  turnId: string | null;
}

export interface AgentGraphState {
  activeAgentIds: string[];
  activeTools: string[];
  modelActive: boolean;
  activeInputId: string | null;
  activeModelId: string | null;
  memoryActive: boolean;
}

export interface SessionState {
  events: AiEventEnvelope[];
  cards: Card[];
  stream: StreamState;
  agentGraph: AgentGraphState;
  lastSeq: number;
}

export const EMPTY_AGENT_GRAPH: AgentGraphState = {
  activeAgentIds: [],
  activeTools: [],
  modelActive: false,
  activeInputId: null,
  activeModelId: null,
  memoryActive: false,
};

export const EMPTY_STREAM: StreamState = {
  messageId: null,
  content: "",
  thinking: "",
  isStreaming: false,
  turnId: null,
};
