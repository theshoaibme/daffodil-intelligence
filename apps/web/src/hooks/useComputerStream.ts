/**
 * useComputerStream — Hook for live screen WebSocket streaming
 */
import { useState, useEffect, useRef, useCallback } from "react";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export interface ScreenFrame {
  frame: string;          // base64 JPEG
  width: number;
  height: number;
  timestamp: number;
  frameNumber: number;
}

export interface ActionLogEntry {
  type: "mouse_move" | "mouse_click" | "keyboard_type" | "hotkey" | "scroll" | "screenshot" | "info";
  description: string;
  timestamp: number;
  x?: number;
  y?: number;
}

export function useComputerStream() {
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [currentFrame, setCurrentFrame] = useState<ScreenFrame | null>(null);
  const [actionLog, setActionLog] = useState<ActionLogEntry[]>([]);
  const [fps, setFps] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isReplaying, setIsReplaying] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const addLog = useCallback((entry: Omit<ActionLogEntry, "timestamp">) => {
    setActionLog((prev) => [
      { ...entry, timestamp: Date.now() },
      ...prev.slice(0, 99),  // Keep last 100
    ]);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/api/computer/screen-stream`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setError(null);
      addLog({ type: "info", description: "Connected to screen stream" });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "frame") {
          setCurrentFrame({
            frame: data.frame,
            width: data.width,
            height: data.height,
            timestamp: data.timestamp,
            frameNumber: data.frame_number || 0,
          });
        }
      } catch (e) {
        console.error("Frame parse error:", e);
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed");
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
      setStreaming(false);
      // Auto-reconnect after 3s
      reconnectTimer.current = setTimeout(connect, 3000);
    };
  }, [addLog]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
    setStreaming(false);
  }, []);

  const startStream = useCallback((targetFps: number = 5) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setFps(targetFps);
    setStreaming(true);
    wsRef.current.send(JSON.stringify({ action: "start", fps: targetFps, quality: 70 }));
    addLog({ type: "info", description: `Screen streaming started at ${targetFps}fps` });
  }, [addLog]);

  const stopStream = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setStreaming(false);
    wsRef.current.send(JSON.stringify({ action: "stop" }));
    addLog({ type: "info", description: "Screen streaming stopped" });
  }, [addLog]);

  // Computer control actions
  const takeScreenshot = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/screenshot`, { method: "POST" });
      const data = await res.json();
      if (data.image) {
        setCurrentFrame({ frame: data.image, width: data.width, height: data.height, timestamp: Date.now(), frameNumber: 0 });
        addLog({ type: "screenshot", description: `Screenshot captured (${data.width}×${data.height})` });
      }
      return data;
    } catch (e: any) {
      addLog({ type: "info", description: `Screenshot failed: ${e.message}` });
      return null;
    }
  }, [API_BASE, addLog]);

  const mouseClick = useCallback(async (x: number, y: number, button: string = "left") => {
    try {
      await fetch(`${API_BASE}/api/computer/mouse/click`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x, y, button }),
      });
      addLog({ type: "mouse_click", description: `Clicked ${button} at (${x}, ${y})`, x, y });
    } catch (e: any) {
      addLog({ type: "info", description: `Click failed: ${e.message}` });
    }
  }, [API_BASE, addLog]);

  const keyboardType = useCallback(async (text: string) => {
    try {
      await fetch(`${API_BASE}/api/computer/keyboard/type`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      addLog({ type: "keyboard_type", description: `Typed: "${text.slice(0, 40)}${text.length > 40 ? "..." : ""}"` });
    } catch (e: any) {
      addLog({ type: "info", description: `Type failed: ${e.message}` });
    }
  }, [API_BASE, addLog]);

  const hotkey = useCallback(async (keys: string[]) => {
    try {
      await fetch(`${API_BASE}/api/computer/keyboard/hotkey`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys }),
      });
      addLog({ type: "hotkey", description: `Hotkey: ${keys.join("+")}` });
    } catch (e: any) {
      addLog({ type: "info", description: `Hotkey failed: ${e.message}` });
    }
  }, [API_BASE, addLog]);

  const startRecording = useCallback(async (name?: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/record/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (data.success) {
        setIsRecording(true);
        addLog({ type: "info", description: `🔴 Recording started${name ? `: ${name}` : ""}` });
      }
      return data;
    } catch (e: any) {
      return { error: e.message };
    }
  }, [API_BASE, addLog]);

  const stopRecording = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/record/stop`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setIsRecording(false);
        addLog({ type: "info", description: `⏹ Recording stopped: ${data.action_count} actions, ${data.duration_seconds?.toFixed(1)}s` });
      }
      return data;
    } catch (e: any) {
      return { error: e.message };
    }
  }, [API_BASE, addLog]);

  const replayRecording = useCallback(async (name?: string, speed: number = 1.0) => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/record/replay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, speed }),
      });
      const data = await res.json();
      if (data.success) {
        setIsReplaying(true);
        addLog({ type: "info", description: `▶️ Replaying: ${data.name} at ${speed}x speed` });
        // Poll until done
        const poll = setInterval(async () => {
          const status = await fetch(`${API_BASE}/api/computer/record/status`).then(r => r.json());
          if (!status.is_replaying) {
            setIsReplaying(false);
            addLog({ type: "info", description: "▶️ Replay complete" });
            clearInterval(poll);
          }
        }, 1000);
      }
      return data;
    } catch (e: any) {
      return { error: e.message };
    }
  }, [API_BASE, addLog]);

  useEffect(() => {
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, []);

  return {
    connected,
    streaming,
    currentFrame,
    actionLog,
    fps,
    error,
    isRecording,
    isReplaying,
    connect,
    disconnect,
    startStream,
    stopStream,
    takeScreenshot,
    mouseClick,
    keyboardType,
    hotkey,
    startRecording,
    stopRecording,
    replayRecording,
  };
}
