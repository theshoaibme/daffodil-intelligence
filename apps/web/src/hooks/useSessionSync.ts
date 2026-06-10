import { useEffect } from "react";
import { eventBus } from "../engine/EventBus";
import type { AiEventEnvelope } from "../engine/types";

/** Multi-tab sync via BroadcastChannel — leader tab holds WS; followers receive events. */
export function useSessionSync(chatId: number | null, isLeader = true) {
  useEffect(() => {
    if (!chatId || typeof BroadcastChannel === "undefined") return;

    const channel = new BroadcastChannel(`daffodil-session-${chatId}`);

    if (isLeader) {
      const unsub = eventBus.subscribe("*", (event: AiEventEnvelope) => {
        if (event.session_id === String(chatId)) {
          channel.postMessage({ type: "event", event });
        }
      });
      return () => {
        unsub();
        channel.close();
      };
    }

    channel.onmessage = (msg) => {
      const data = msg.data as { type: string; event?: AiEventEnvelope };
      if (data.type === "event" && data.event) {
        eventBus.publishImmediate(data.event);
      }
    };

    return () => channel.close();
  }, [chatId, isLeader]);
}
