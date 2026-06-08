import React, { useRef, useEffect, useState, useCallback } from "react";
import { useComputerStream } from "../../../hooks/useComputerStream";
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
  Clock,
  ChevronRight,
  ChevronLeft,
  Settings
} from "lucide-react";

// ─── Action Log ─────────────────────────────────────────────────────────────

const actionIcons: Record<string, string> = {
  mouse_click: "🖱️",
  mouse_move: "↗️",
  keyboard_type: "⌨️",
  hotkey: "⚡",
  scroll: "↕️",
  screenshot: "📸",
  info: "ℹ️",
};

function ActionLog({ entries }: { entries: any[] }) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-on-surface-variant/50 gap-2">
        <Zap size={24} />
        <span className="text-sm">Actions will appear here</span>
      </div>
    );
  }

  return (
    <div ref={listRef} className="space-y-1 overflow-y-auto max-h-60 pr-1 custom-scrollbar">
      {entries.map((entry, i) => {
        const icon = actionIcons[entry.type] || "•";
        const time = new Date(entry.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
        return (
          <div
            key={i}
            className="flex items-start gap-2 py-1.5 px-2 rounded-lg hover:bg-surface-container-high/50 transition-colors"
          >
            <span className="text-base leading-5 shrink-0">{icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-on-surface truncate">{entry.description}</p>
              <p className="text-[10px] text-on-surface-variant/60">{time}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

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
          <p className="text-sm mt-1">Open the side panel and connect to begin</p>
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

// ─── Main ComputerView Page ──────────────────────────────────────────────────

export default function ComputerView() {
  const {
    connected,
    streaming,
    currentFrame,
    actionLog,
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
  const [panelOpen, setPanelOpen] = useState(false);
  const [typeText, setTypeText] = useState("");

  const handleCanvasClick = useCallback(
    (x: number, y: number) => {
      if (clickMode) {
        mouseClick(x, y);
      }
    },
    [clickMode, mouseClick]
  );

  return (
    <div className="relative w-full h-screen bg-black overflow-hidden flex">
      
      {/* Background Canvas Layer */}
      <div className="flex-1 relative">
        <ScreenViewer frame={currentFrame} onCanvasClick={handleCanvasClick} />
        
        {/* Error Toast */}
        {error && (
          <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-error text-on-error px-4 py-2 rounded-full shadow-lg z-50 flex items-center gap-2 animate-in fade-in slide-in-from-top-4">
            <Zap size={16} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        {/* Floating Quick Action Bar (Bottom Center) */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-surface-container-lowest/90 backdrop-blur-md p-2 rounded-2xl shadow-xl border border-outline-variant/50 transition-all hover:shadow-2xl z-40">
          
          <button
            onClick={() => setClickMode(v => !v)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              clickMode ? "bg-primary text-on-primary" : "text-on-surface hover:bg-surface-container-high"
            }`}
          >
            <MousePointer2 size={16} />
            Click Mode
          </button>
          
          <div className="w-px h-6 bg-outline-variant/50 mx-1" />

          {isRecording ? (
            <button
              onClick={stopRecording}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-error text-on-error animate-pulse"
            >
              <Circle size={16} fill="currentColor" />
              Stop Recording
            </button>
          ) : (
            <button
              onClick={() => startRecording()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-on-surface hover:bg-surface-container-high"
            >
              <Circle size={16} />
              Record
            </button>
          )}

          <button
            onClick={() => replayRecording()}
            disabled={isReplaying}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium ${
              isReplaying ? "bg-primary/20 text-primary" : "text-on-surface hover:bg-surface-container-high"
            }`}
          >
            <RotateCcw size={16} className={isReplaying ? "animate-spin" : ""} />
            Replay
          </button>
        </div>
      </div>

      {/* Floating Panel Toggle Button */}
      <button
        onClick={() => setPanelOpen(!panelOpen)}
        className={`absolute top-1/2 -translate-y-1/2 right-0 flex items-center justify-center w-8 h-16 bg-surface-container-lowest/80 backdrop-blur border border-r-0 border-outline-variant rounded-l-2xl shadow-lg z-50 hover:bg-surface-container transition-transform ${panelOpen ? 'translate-x-full opacity-0' : 'translate-x-0'}`}
      >
        <ChevronLeft size={20} className="text-on-surface" />
      </button>

      {/* Sliding Control Panel */}
      <div 
        className={`absolute top-0 right-0 h-full w-80 bg-surface-container-lowest/95 backdrop-blur-xl border-l border-outline-variant/50 shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${panelOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {/* Panel Header */}
        <div className="flex items-center justify-between p-4 border-b border-outline-variant/30">
          <div className="flex items-center gap-2 text-on-surface">
            <Settings size={18} />
            <h2 className="font-semibold">Controls</h2>
          </div>
          <button 
            onClick={() => setPanelOpen(false)}
            className="p-1.5 rounded-lg hover:bg-surface-container-high text-on-surface-variant transition-colors"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Panel Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          {/* Connection controls */}
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Connection</p>
            <button
              onClick={connected ? disconnect : connect}
              className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                connected
                  ? "bg-error/10 text-error hover:bg-error/20"
                  : "bg-primary text-on-primary hover:bg-primary/90 shadow-md hover:shadow-lg"
              }`}
            >
              {connected ? <WifiOff size={16} /> : <Wifi size={16} />}
              {connected ? "Disconnect" : "Connect"}
            </button>

            <button
              onClick={streaming ? stopStream : () => startStream(5)}
              disabled={!connected}
              className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-40 ${
                streaming
                  ? "bg-tertiary/10 text-tertiary hover:bg-tertiary/20"
                  : "bg-surface-container text-on-surface hover:bg-surface-container-high"
              }`}
            >
              {streaming ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
              {streaming ? "Stop Stream" : "Live Stream"}
            </button>
          </div>

          {/* Tools */}
          <div className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Tools</p>
            
            <button
              onClick={takeScreenshot}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium bg-surface-container hover:bg-surface-container-high transition-all"
            >
              <Camera size={16} className="text-primary" />
              Take Screenshot
            </button>

            <div className="bg-surface-container rounded-xl p-3 space-y-2">
              <label className="text-xs font-medium text-on-surface flex items-center gap-2">
                <Keyboard size={14} /> Send Text Input
              </label>
              <div className="flex gap-2">
                <input
                  value={typeText}
                  onChange={(e) => setTypeText(e.target.value)}
                  placeholder="Type here..."
                  className="flex-1 px-3 py-2 text-sm rounded-lg bg-surface-container-highest focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-on-surface-variant/50"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && typeText) {
                      keyboardType(typeText);
                      setTypeText("");
                    }
                  }}
                />
                <button
                  onClick={() => {
                    if (typeText) {
                      keyboardType(typeText);
                      setTypeText("");
                    }
                  }}
                  disabled={!typeText}
                  className="px-3 py-2 rounded-lg bg-primary text-on-primary text-sm font-medium disabled:opacity-50"
                >
                  Send
                </button>
              </div>
            </div>
          </div>

          {/* Action Log inline in the panel */}
          <div className="pt-4 border-t border-outline-variant/30">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-3">
              <Clock size={14} />
              Action Log
            </div>
            <div className="bg-surface-container rounded-xl p-2">
              <ActionLog entries={actionLog} />
            </div>
          </div>

        </div>
      </div>

    </div>
  );
}
