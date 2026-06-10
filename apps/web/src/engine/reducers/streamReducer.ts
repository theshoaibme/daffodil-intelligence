import type { AiEventEnvelope, StreamState } from "../types";

export function streamReducer(state: StreamState, events: AiEventEnvelope[]): StreamState {
  let next = { ...state };

  for (const event of events) {
    if (event.type === "message.chunk") {
      const chunk = String(event.payload.content ?? "");
      next = {
        ...next,
        content: next.content + chunk,
        isStreaming: true,
        turnId: event.turn_id,
      };
    }

    if (event.type === "message.thinking") {
      const chunk = String(event.payload.content ?? "");
      next = {
        ...next,
        thinking: next.thinking + chunk,
        isStreaming: true,
        turnId: event.turn_id,
      };
    }

    if (event.type === "message.completed" || event.type === "stream.done") {
      next = { ...next, isStreaming: false };
    }

    if (event.type === "stream.cancelled") {
      next = { ...next, isStreaming: false };
    }
  }

  return next;
}

export function resetStream(turnId: string | null, messageId: string | null): StreamState {
  return {
    messageId,
    content: "",
    thinking: "",
    isStreaming: true,
    turnId,
  };
}
