import { useCallback, useEffect, useRef } from "react";
import { eventBus } from "../engine/EventBus";
import { useEventStore } from "../engine/stores/eventStore";
import type { AiEventEnvelope } from "../engine/types";
import { getAuthHeaders } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_URL || "";

function wsUrl(chatId: number): string {
  const base = API_BASE.replace(/\/$/, "") || `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
  const proto = base.startsWith("https") ? "wss" : "ws";
  const host = base.replace(/^https?:\/\//, "");
  return `${proto}://${host}/api/sessions/${chatId}/events/ws`;
}

export function useSessionStream(chatId: number | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const backoffRef = useRef(1000);

  const replayFromSeq = useCallback(async (fromSeq: number) => {
    if (!chatId) return;
    const base = API_BASE.replace(/\/$/, "");
    const res = await fetch(`${base}/api/sessions/${chatId}/events?from_seq=${fromSeq}`, {
      headers: getAuthHeaders() as HeadersInit,
    });
    if (!res.ok) return;
    const data = (await res.json()) as { events: AiEventEnvelope[] };
    for (const event of data.events ?? []) {
      eventBus.publish(event);
    }
  }, [chatId]);

  useEffect(() => {
    if (!chatId) return;

    let closed = false;

    const connect = () => {
      if (closed) return;
      const ws = new WebSocket(wsUrl(chatId));
      wsRef.current = ws;

      ws.onopen = () => {
        backoffRef.current = 1000;
        const lastSeq = useEventStore.getState().getSession(String(chatId)).lastSeq;
        ws.send(JSON.stringify({ type: "sync.request", from_seq: lastSeq }));
        if (lastSeq > 0) void replayFromSeq(lastSeq);
      };

      ws.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data) as Record<string, unknown>;
          if (parsed.envelope) {
            eventBus.publish(parsed.envelope as AiEventEnvelope);
          }
        } catch {
          // ignore
        }
      };

      ws.onclose = () => {
        if (closed) return;
        reconnectTimer.current = setTimeout(() => {
          backoffRef.current = Math.min(backoffRef.current * 2, 30000);
          connect();
        }, backoffRef.current);
      };
    };

    connect();

    return () => {
      closed = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [chatId, replayFromSeq]);

  return { replayFromSeq };
}
