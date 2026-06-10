import { useState, useCallback, useEffect } from "react";
import { useComputerStream } from "./useComputerStream";
import { useKit } from "./useKit";
import { useMouseTracker } from "./useMouseTracker";
import type { ActionLogEntry, ScreenFrame } from "./useComputerStream";
import type { KitPermissions } from "./useKit";

export interface CopycatModeState {
  // Connection
  connected: boolean;
  streaming: boolean;
  kitOnline: boolean;
  error: string | null;

  // Frame
  currentFrame: ScreenFrame | null;
  fps: number;

  // Input modes
  clickMode: boolean;
  keyboardOpen: boolean;
  focusMode: boolean;

  // CopyCat state
  isRecording: boolean;
  isReplaying: boolean;
  copycatBlocked: boolean;
  copycatMessage: string | null;

  // Mouse tracking
  mousePosition: { x: number; y: number } | null;
  mouseTrail: Array<{ x: number; y: number; t: number }>;
  lastClick: { x: number; y: number } | null;
  mouseTrackerConnected: boolean;

  // Action log
  actionLog: ActionLogEntry[];

  // Kit
  permissions: KitPermissions | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  toggleStream: () => void;
  toggleClickMode: () => void;
  toggleKeyboard: () => void;
  toggleFocusMode: () => void;
  takeScreenshot: () => Promise<unknown>;
  sendMouseClick: (x: number, y: number) => void;
  sendKeyboardText: (text: string) => void;
  sendHotkey: (keys: string[]) => void;
  startRecording: (name?: string) => Promise<unknown>;
  stopRecording: () => Promise<unknown>;
  replayRecording: (name?: string, speed?: number, skipMoves?: boolean) => Promise<unknown>;
  stopReplay: () => Promise<unknown>;
  refreshKit: () => void;
  enableFocusCapture: () => Promise<unknown>;
  configureStream: (config: Record<string, unknown>) => void;
  clearActionLog: () => void;
  sendChatAction: (command: string) => void;
}

export function useCopycatMode(active: boolean = false): CopycatModeState {
  const stream = useComputerStream();
  const kit = useKit();
  const mouseTracker = useMouseTracker(active && stream.streaming);

  const [clickMode, setClickMode] = useState(false);
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const [focusMode, setFocusMode] = useState(false);

  // Auto-connect when mode becomes active
  useEffect(() => {
    if (active && !stream.connected) {
      stream.connect();
    }
    if (!active && stream.connected) {
      stream.disconnect();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]); // intentionally not tracking stream to avoid loops

  // Disable input modes when CopyCat is blocking
  useEffect(() => {
    if (stream.copycatBlocked) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setClickMode(false);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setKeyboardOpen(false);
    }
  }, [stream.copycatBlocked]);

  const toggleStream = useCallback(() => {
    if (stream.streaming) {
      stream.stopStream();
    } else {
      stream.startStream({ focus_mode: focusMode });
    }
  }, [stream, focusMode]);

  const toggleClickMode = useCallback(() => {
    setClickMode((v) => !v);
  }, []);

  const toggleKeyboard = useCallback(() => {
    setKeyboardOpen((v) => !v);
  }, []);

  const toggleFocusMode = useCallback(async () => {
    const next = !focusMode;
    setFocusMode(next);
    stream.configureStream({ focus_mode: next });
    if (next) await kit.enableFocusCapture();
  }, [focusMode, stream, kit]);

  const sendMouseClick = useCallback(
    (x: number, y: number) => {
      if (stream.copycatBlocked || !clickMode) return;
      stream.mouseClick(x, y);
    },
    [stream, clickMode]
  );

  const sendKeyboardText = useCallback(
    (text: string) => {
      stream.keyboardType(text);
    },
    [stream]
  );

  const sendHotkey = useCallback(
    (keys: string[]) => {
      stream.hotkey(keys);
    },
    [stream]
  );

  const replayRecording = useCallback(
    async (name?: string, speed = 2.0) => {
      return stream.replayRecording(name, speed);
    },
    [stream]
  );

  const clearActionLog = useCallback(() => {
    // Managed inside stream
  }, []);

  return {
    // Connection
    connected: stream.connected,
    streaming: stream.streaming,
    kitOnline: kit.kitOnline,
    error: stream.error,

    // Frame
    currentFrame: stream.currentFrame,
    fps: stream.fps,

    // Input modes
    clickMode,
    keyboardOpen,
    focusMode,

    // CopyCat
    isRecording: stream.isRecording,
    isReplaying: stream.isReplaying,
    copycatBlocked: stream.copycatBlocked,
    copycatMessage: stream.copycatMessage,

    // Mouse tracking
    mousePosition: mouseTracker.position,
    mouseTrail: mouseTracker.trail,
    lastClick: mouseTracker.lastClick,
    mouseTrackerConnected: mouseTracker.connected,

    // Action log
    actionLog: stream.actionLog,

    // Kit
    permissions: kit.permissions,

    // Actions
    connect: stream.connect,
    disconnect: stream.disconnect,
    toggleStream,
    toggleClickMode,
    toggleKeyboard,
    toggleFocusMode,
    takeScreenshot: stream.takeScreenshot,
    sendMouseClick,
    sendKeyboardText,
    sendHotkey,
    startRecording: stream.startRecording,
    stopRecording: stream.stopRecording,
    replayRecording,
    stopReplay: stream.stopReplay,
    refreshKit: kit.refresh,
    enableFocusCapture: kit.enableFocusCapture,
    configureStream: stream.configureStream,
    clearActionLog,
    sendChatAction: stream.sendChatAction,
  };
}
