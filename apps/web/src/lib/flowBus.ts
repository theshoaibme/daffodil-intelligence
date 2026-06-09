/**
 * Live agent-flow bus.
 *
 * `useChat` publishes the active agent / tools / model while a turn streams,
 * and the AgentFlowCanvas subscribes so the graph highlights what is running
 * in real time. Module-level so it works across the component tree without
 * prop drilling.
 */

export interface FlowState {
  activeAgentIds: string[];
  activeTools: string[];
  modelActive: boolean;
  activeModelId?: string;
}

const EMPTY: FlowState = {
  activeAgentIds: [],
  activeTools: [],
  modelActive: false,
};

let state: FlowState = EMPTY;
const listeners = new Set<(s: FlowState) => void>();

export function getFlow(): FlowState {
  return state;
}

export function emitFlow(partial: Partial<FlowState>): void {
  state = { ...state, ...partial };
  listeners.forEach((fn) => fn(state));
}

export function resetFlow(): void {
  state = EMPTY;
  listeners.forEach((fn) => fn(state));
}

export function subscribeFlow(fn: (s: FlowState) => void): () => void {
  listeners.add(fn);
  fn(state);
  return () => {
    listeners.delete(fn);
  };
}
