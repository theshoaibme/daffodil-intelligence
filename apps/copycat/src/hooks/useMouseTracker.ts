/**
 * useMouseTracker — WebSocket-based real-time mouse position streaming
 */
import { useState, useEffect, useRef, useCallback } from "react";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export interface MousePosition {
  x: number;
  y: number;
}

export interface TrailPoint extends MousePosition {
  t: number;
}

const MAX_TRAIL = 50;

export function useMouseTracker(enabled: boolean = false) {
  const [position, setPosition] = useState<MousePosition | null>(null);
  const [trail, setTrail] = useState<TrailPoint[]>([]);
  const [lastClick, setLastClick] = useState<MousePosition | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (!enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_BASE}/api/computer/mouse-position`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "position") {
            const pos = { x: data.x, y: data.y };
            setPosition(pos);
            setTrail((prev) => {
              const next = [...prev, { ...pos, t: data.timestamp || Date.now() }];
              return next.length > MAX_TRAIL ? next.slice(-MAX_TRAIL) : next;
            });
          } else if (data.type === "click") {
            setLastClick({ x: data.x, y: data.y });
          }
        } catch {
          /* ignore */
        }
      };

      ws.onerror = () => {
        setConnected(false);
      };

      ws.onclose = () => {
        setConnected(false);
        if (enabled) {
          reconnectTimer.current = setTimeout(connect, 3000);
        }
      };
    } catch {
      /* ignore */
    }
  }, [enabled]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
    setPosition(null);
    setTrail([]);
  }, []);

  // Auto-connect when enabled
  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }
    return () => disconnect();
  }, [enabled, connect, disconnect]);

  const clearTrail = useCallback(() => {
    setTrail([]);
    setLastClick(null);
  }, []);

  return {
    position,
    trail,
    lastClick,
    connected,
    clearTrail,
  };
}
