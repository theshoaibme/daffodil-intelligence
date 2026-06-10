import { create } from "zustand";
import { eventBus } from "../EventBus";
import { agentGraphReducer } from "../reducers/agentGraphReducer";
import { cardsReducer, clearCardsForTurn } from "../reducers/cardsReducer";
import { resetStream, streamReducer } from "../reducers/streamReducer";
import type { AiEventEnvelope, SessionState } from "../types";
import { EMPTY_AGENT_GRAPH, EMPTY_STREAM } from "../types";

function emptySession(): SessionState {
  return {
    events: [],
    cards: [],
    stream: { ...EMPTY_STREAM },
    agentGraph: { ...EMPTY_AGENT_GRAPH },
    lastSeq: 0,
  };
}

interface EventStore {
  sessions: Record<string, SessionState>;
  getSession: (sessionId: string) => SessionState;
  appendEvents: (sessionId: string, events: AiEventEnvelope[]) => void;
  resetTurn: (sessionId: string, turnId: string, messageId?: string | null) => void;
  clearSession: (sessionId: string) => void;
  setActiveInput: (sessionId: string, inputId: string | null) => void;
}

function mergeEvents(events: AiEventEnvelope[]): AiEventEnvelope[] {
  const out: AiEventEnvelope[] = [];
  for (const e of events) {
    const prev = out[out.length - 1];
    if (
      prev &&
      prev.type === "message.chunk" &&
      e.type === "message.chunk" &&
      prev.turn_id === e.turn_id
    ) {
      out[out.length - 1] = {
        ...prev,
        payload: {
          ...prev.payload,
          content: String(prev.payload.content ?? "") + String(e.payload.content ?? ""),
        },
      };
    } else {
      out.push(e);
    }
  }
  return out;
}

export const useEventStore = create<EventStore>((set, get) => ({
  sessions: {},

  getSession(sessionId) {
    return get().sessions[sessionId] ?? emptySession();
  },

  appendEvents(sessionId, events) {
    if (!events.length) return;
    set((state) => {
      const current = state.sessions[sessionId] ?? emptySession();
      const merged = mergeEvents(events);
      const lastSeq = Math.max(current.lastSeq, ...merged.map((e) => e.seq));
      return {
        sessions: {
          ...state.sessions,
          [sessionId]: {
            events: [...current.events, ...merged],
            cards: cardsReducer(current.cards, merged),
            stream: streamReducer(current.stream, merged),
            agentGraph: agentGraphReducer(current.agentGraph, merged),
            lastSeq,
          },
        },
      };
    });
  },

  resetTurn(sessionId, turnId, messageId = null) {
    set((state) => {
      const current = state.sessions[sessionId] ?? emptySession();
      return {
        sessions: {
          ...state.sessions,
          [sessionId]: {
            ...current,
            cards: clearCardsForTurn(current.cards, turnId),
            stream: resetStream(turnId, messageId),
            agentGraph: { ...EMPTY_AGENT_GRAPH, activeInputId: current.agentGraph.activeInputId },
          },
        },
      };
    });
  },

  clearSession(sessionId) {
    set((state) => {
      const next = { ...state.sessions };
      delete next[sessionId];
      return { sessions: next };
    });
  },

  setActiveInput(sessionId, inputId) {
    set((state) => {
      const current = state.sessions[sessionId] ?? emptySession();
      return {
        sessions: {
          ...state.sessions,
          [sessionId]: {
            ...current,
            agentGraph: { ...current.agentGraph, activeInputId: inputId },
          },
        },
      };
    });
  },
}));

eventBus.setFlushCallback((events) => {
  const bySession = new Map<string, AiEventEnvelope[]>();
  for (const e of events) {
    const list = bySession.get(e.session_id) ?? [];
    list.push(e);
    bySession.set(e.session_id, list);
  }
  for (const [sessionId, batch] of bySession) {
    useEventStore.getState().appendEvents(sessionId, batch);
  }
});
