/**
 * useComputerStream — adaptive kit-aware screen streaming
 */
import { useState, useEffect, useRef, useCallback } from "react";
import type { StreamConfig } from "./useKit";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ScreenFrame {
  frame: string;
  width: number;
  height: number;
  timestamp: number;
  frameNumber: number;
  fps?: number;
  latency_ms?: number;
  backend?: string;
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
  const [fps, setFps] = useState(12);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isReplaying, setIsReplaying] = useState(false);
  const [copycatMessage, setCopycatMessage] = useState<string | null>(null);
  const [streamConfig, setStreamConfig] = useState<StreamConfig>({
    max_fps: 30,
    min_fps: 8,
    max_quality: 70,
    target_latency_ms: 80,
    focus_mode: false,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const addLog = useCallback((entry: Omit<ActionLogEntry, "timestamp">) => {
    setActionLog((prev) => [{ ...entry, timestamp: Date.now() }, ...prev.slice(0, 99)]);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/api/computer/screen-stream`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setError(null);
      addLog({ type: "info", description: "Connected — adaptive stream ready" });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "frame") {
          if (data.fps) setFps(data.fps);
          setCurrentFrame({
            frame: data.frame,
            width: data.width,
            height: data.height,
            timestamp: data.timestamp,
            frameNumber: data.frame_number || 0,
            fps: data.fps,
            latency_ms: data.latency_ms,
            backend: data.backend,
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
      reconnectTimer.current = setTimeout(connect, 2000);
    };
  }, [addLog]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
    setStreaming(false);
  }, []);

  const startStream = useCallback(
    (config?: StreamConfig) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      const cfg = { ...streamConfig, ...config };
      setStreamConfig(cfg);
      setStreaming(true);
      wsRef.current.send(JSON.stringify({ action: "start", config: cfg }));
      addLog({ type: "info", description: `Adaptive stream · focus=${!!cfg.focus_mode}` });
    },
    [addLog, streamConfig]
  );

  const stopStream = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setStreaming(false);
    wsRef.current.send(JSON.stringify({ action: "stop" }));
    addLog({ type: "info", description: "Stream stopped" });
  }, [addLog]);

  const configureStream = useCallback(
    (config: StreamConfig) => {
      const cfg = { ...streamConfig, ...config };
      setStreamConfig(cfg);
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "configure", config: cfg }));
      }
    },
    [streamConfig]
  );

  const takeScreenshot = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/screenshot`, { method: "POST" });
      const data = await res.json();
      if (data.image) {
        setCurrentFrame({
          frame: data.image,
          width: data.width,
          height: data.height,
          timestamp: Date.now(),
          frameNumber: 0,
        });
        addLog({ type: "screenshot", description: `Screenshot (${data.width}×${data.height})` });
      }
      return data;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "failed";
      addLog({ type: "info", description: `Screenshot failed: ${msg}` });
      return null;
    }
  }, [addLog]);

  const copycatBlocked = isReplaying || !!copycatMessage;

  const mouseClick = useCallback(
    async (x: number, y: number, button = "left") => {
      if (copycatBlocked) {
        addLog({ type: "info", description: "CopyCat is running — click blocked" });
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/computer/mouse/click`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ x, y, button }),
        });
        if (res.status === 423) {
          const data = await res.json();
          setCopycatMessage(data.detail?.message || "CopyCat is running");
          addLog({ type: "info", description: "CopyCat is running — click blocked" });
          return;
        }
        addLog({ type: "mouse_click", description: `Click ${button} (${x}, ${y})`, x, y });
      } catch {
        addLog({ type: "info", description: "Click failed" });
      }
    },
    [addLog, copycatBlocked]
  );

  const keyboardType = useCallback(
    async (text: string) => {
      if (copycatBlocked) {
        addLog({ type: "info", description: "CopyCat is running — keyboard blocked" });
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/computer/keyboard/type`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        if (res.status === 423) {
          const data = await res.json();
          setCopycatMessage(data.detail?.message || "CopyCat is running");
          addLog({ type: "info", description: "CopyCat is running — keyboard blocked" });
          return;
        }
        addLog({ type: "keyboard_type", description: `Typed: ${text.slice(0, 40)}` });
      } catch {
        addLog({ type: "info", description: "Type failed" });
      }
    },
    [addLog, copycatBlocked]
  );

  const hotkey = useCallback(
    async (keys: string[]) => {
      await fetch(`${API_BASE}/api/computer/keyboard/hotkey`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys }),
      });
      addLog({ type: "hotkey", description: keys.join("+") });
    },
    [addLog]
  );

  const startRecording = useCallback(
    async (name?: string) => {
      const res = await fetch(`${API_BASE}/api/computer/record/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (data.success) {
        setIsRecording(true);
        addLog({ type: "info", description: `Recording started` });
      }
      return data;
    },
    [addLog]
  );

  const stopRecording = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/computer/record/stop`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      setIsRecording(false);
      addLog({ type: "info", description: `Stopped · ${data.action_count} actions` });
    }
    return data;
  }, [addLog]);

  const stopReplay = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/computer/record/stop-replay`, { method: "POST" });
    const data = await res.json();
    setIsReplaying(false);
    setCopycatMessage(null);
    addLog({ type: "info", description: data.stopped ? "CopyCat replay stopped" : "No replay active" });
    return data;
  }, [addLog]);

  const replayRecording = useCallback(
    async (name?: string, speed = 2.0) => {
      const res = await fetch(`${API_BASE}/api/computer/record/replay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, speed, skip_mouse_moves: true }),
      });
      const data = await res.json();
      if (data.success) {
        setIsReplaying(true);
        setCopycatMessage("CopyCat is running — mouse and keyboard are disabled");
      }
      return data;
    },
    []
  );

  useEffect(() => {
    let poll: ReturnType<typeof setInterval> | undefined;
    const checkStatus = async () => {
      try {
        const status = await fetch(`${API_BASE}/api/computer/record/status`).then((r) => r.json());
        const active = status.copycat_running || status.is_replaying;
        setIsReplaying(!!status.is_replaying);
        setCopycatMessage(active ? status.message || "CopyCat is running" : null);
      } catch {
        /* ignore */
      }
    };
    poll = setInterval(checkStatus, 500);
    checkStatus();
    return () => clearInterval(poll);
  }, []);

  useEffect(() => () => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
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
    copycatMessage,
    copycatBlocked,
    streamConfig,
    connect,
    disconnect,
    startStream,
    stopStream,
    configureStream,
    takeScreenshot,
    mouseClick,
    keyboardType,
    hotkey,
    startRecording,
    stopRecording,
    replayRecording,
    stopReplay,
  };
}
