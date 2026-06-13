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
  /** Left input node: input-chat | input-telegram */
  activeInputId?: string | null;
  /** Right memory node highlight */
  memoryActive?: boolean;
}

const EMPTY: FlowState = {
  activeAgentIds: [],
  activeTools: [],
  modelActive: false,
  activeInputId: null,
  memoryActive: false,
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

/** Replace entire flow state (avoids stale keys from partial merges). */
export function setFlow(next: FlowState): void {
  state = { ...next };
  listeners.forEach((fn) => fn(state));
}

export function resetFlow(): void {
  state = { ...EMPTY };
  listeners.forEach((fn) => fn(state));
}

export function subscribeFlow(fn: (s: FlowState) => void): () => void {
  listeners.add(fn);
  fn(state);
  return () => {
    listeners.delete(fn);
  };
}
