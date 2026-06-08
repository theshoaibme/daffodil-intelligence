import React, { useRef, useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useComputerStream } from "../../../hooks/useComputerStream";
import { ROUTES } from "../../../lib/routes";
import {
  Monitor,
  Camera,
  Play,
  Square,
  Circle,
  Wifi,
  WifiOff,
  MousePointer2,
  Keyboard,
  Zap,
  RotateCcw,
  MessageSquare,
  Send,
} from "lucide-react";

// ─── Screen Viewer ───────────────────────────────────────────────────────────

function ScreenViewer({
  frame,
  onCanvasClick,
}: {
  frame: { frame: string; width: number; height: number } | null;
  onCanvasClick: (x: number, y: number) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!frame || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = frame.width;
      canvas.height = frame.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = `data:image/jpeg;base64,${frame.frame}`;
  }, [frame]);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !frame) return;
      const rect = canvasRef.current.getBoundingClientRect();
      const scaleX = frame.width / rect.width;
      const scaleY = frame.height / rect.height;
      const x = Math.round((e.clientX - rect.left) * scaleX);
      const y = Math.round((e.clientY - rect.top) * scaleY);
      onCanvasClick(x, y);
    },
    [frame, onCanvasClick]
  );

  if (!frame) {
    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-on-surface-variant/50">
        <Monitor size={64} strokeWidth={1} />
        <div className="text-center">
          <p className="font-medium text-on-surface/70 text-lg">No connection</p>
          <p className="text-sm mt-1">Use the toolbar below to connect</p>
        </div>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full object-contain cursor-crosshair bg-black"
      style={{ imageRendering: "pixelated" }}
      onClick={handleClick}
      title="Click to send mouse click to this position"
    />
  );
}

// ─── Icon Toolbar Button ─────────────────────────────────────────────────────

function ToolbarButton({
  onClick,
  active,
  disabled,
  danger,
  label,
  children,
}: {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  danger?: boolean;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`w-8 h-8 flex items-center justify-center rounded-full transition-all disabled:opacity-40 ${
        active
          ? "bg-primary text-on-primary"
          : danger
            ? "text-error hover:bg-error/15"
            : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
      }`}
    >
      {children}
    </button>
  );
}

// ─── Main ComputerView Page ──────────────────────────────────────────────────

export interface ComputerViewProps {
  embedded?: boolean;
  onExitCopycat?: () => void;
}

export default function ComputerView({ embedded = false, onExitCopycat }: ComputerViewProps) {
  const navigate = useNavigate();
  const {
    connected,
    streaming,
    currentFrame,
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
    startRecording,
    stopRecording,
    replayRecording,
  } = useComputerStream();

  const [clickMode, setClickMode] = useState(false);
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const [typeText, setTypeText] = useState("");

  const handleCanvasClick = useCallback(
    (x: number, y: number) => {
      if (clickMode) {
        mouseClick(x, y);
      }
    },
    [clickMode, mouseClick]
  );

  const handleChatClick = () => {
    if (onExitCopycat) {
      onExitCopycat();
    } else {
      navigate(ROUTES.home);
    }
  };

  const sendText = () => {
    if (typeText) {
      keyboardType(typeText);
      setTypeText("");
      setKeyboardOpen(false);
    }
  };

  return (
    <div
      className={`relative w-full bg-black overflow-hidden flex ${
        embedded ? "absolute inset-0 z-40" : "h-screen"
      }`}
    >
      <div className="flex-1 relative">
        <ScreenViewer frame={currentFrame} onCanvasClick={handleCanvasClick} />

        {error && (
          <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-error text-on-error px-4 py-2 rounded-full shadow-lg z-50 flex items-center gap-2">
            <Zap size={16} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}
      </div>

      {/* Keyboard input popover */}
      {keyboardOpen && (
        <div className="fixed bottom-20 left-0 right-0 z-50 flex justify-center w-full px-4 pointer-events-none">
          <div className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 rounded-3xl p-3 shadow-md flex gap-2 pointer-events-auto">
            <input
              value={typeText}
              onChange={(e) => setTypeText(e.target.value)}
              placeholder="Type text to send…"
              autoFocus
              className="flex-1 px-3 py-2 text-sm rounded-xl bg-surface-container-highest focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-on-surface-variant/50"
              onKeyDown={(e) => {
                if (e.key === "Enter") sendText();
                if (e.key === "Escape") setKeyboardOpen(false);
              }}
            />
            <button
              type="button"
              onClick={sendText}
              disabled={!typeText}
              aria-label="Send text"
              className="w-10 h-10 flex items-center justify-center rounded-xl bg-primary text-on-primary disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Bottom icon toolbar — same position as chat PromptBar */}
      <div className="fixed bottom-6 left-0 right-0 z-50 flex justify-center w-full px-4 pointer-events-none">
        <div className="glass-gradient-panel border border-outline-variant/40 inline-flex items-center justify-center gap-0.5 rounded-full px-1.5 py-1 shadow-md pointer-events-auto">
          <ToolbarButton onClick={handleChatClick} label="Back to chat">
            <MessageSquare size={16} />
          </ToolbarButton>

          <ToolbarButton
            onClick={() => (connected ? disconnect() : connect())}
            active={connected}
            label={connected ? "Disconnect" : "Connect"}
          >
            {connected ? <Wifi size={16} /> : <WifiOff size={16} />}
          </ToolbarButton>

          <ToolbarButton
            onClick={() => (streaming ? stopStream() : startStream(5))}
            active={streaming}
            disabled={!connected}
            label={streaming ? "Stop stream" : "Live stream"}
          >
            {streaming ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
          </ToolbarButton>

          <ToolbarButton
            onClick={() => setClickMode((v) => !v)}
            active={clickMode}
            label="Click mode"
          >
            <MousePointer2 size={16} />
          </ToolbarButton>

          <ToolbarButton onClick={takeScreenshot} label="Screenshot">
            <Camera size={16} />
          </ToolbarButton>

          <ToolbarButton
            onClick={() => setKeyboardOpen((v) => !v)}
            active={keyboardOpen}
            label="Keyboard input"
          >
            <Keyboard size={16} />
          </ToolbarButton>

          {isRecording ? (
            <ToolbarButton onClick={stopRecording} danger label="Stop recording">
              <Circle size={16} fill="currentColor" />
            </ToolbarButton>
          ) : (
            <ToolbarButton onClick={() => startRecording()} label="Record">
              <Circle size={16} />
            </ToolbarButton>
          )}

          <ToolbarButton
            onClick={() => replayRecording()}
            disabled={isReplaying}
            active={isReplaying}
            label="Replay"
          >
            <RotateCcw size={16} className={isReplaying ? "animate-spin" : ""} />
          </ToolbarButton>
        </div>
      </div>
    </div>
  );
}
