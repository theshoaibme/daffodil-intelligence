import React, { useRef, useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useComputerStream } from "../../../hooks/useComputerStream";
import { useKit } from "../../../hooks/useKit";
import { KitToolbar } from "./KitToolbar";
import { ROUTES } from "../../../lib/routes";
import { modeSpring, modeSpringSoft, overlayFade } from "../../../lib/motion";
import { AlertTriangle, Monitor, Zap, Send, Square } from "lucide-react";

// ─── Screen Viewer ───────────────────────────────────────────────────────────

function ScreenViewer({
  frame,
  onCanvasClick,
  inputBlocked,
}: {
  frame: { frame: string; width: number; height: number } | null;
  onCanvasClick: (x: number, y: number) => void;
  inputBlocked?: boolean;
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
      if (inputBlocked || !canvasRef.current || !frame) return;
      const rect = canvasRef.current.getBoundingClientRect();
      const scaleX = frame.width / rect.width;
      const scaleY = frame.height / rect.height;
      const x = Math.round((e.clientX - rect.left) * scaleX);
      const y = Math.round((e.clientY - rect.top) * scaleY);
      onCanvasClick(x, y);
    },
    [frame, onCanvasClick, inputBlocked]
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
      className={`absolute inset-0 w-full h-full object-contain bg-black ${
        inputBlocked ? "cursor-not-allowed pointer-events-none" : "cursor-crosshair"
      }`}
      style={{ imageRendering: "pixelated" }}
      onClick={handleClick}
      title={inputBlocked ? "CopyCat is running — input disabled" : "Click to send mouse click to this position"}
    />
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
    copycatMessage,
    copycatBlocked,
    connect,
    disconnect,
    startStream,
    stopStream,
    configureStream,
    takeScreenshot,
    mouseClick,
    keyboardType,
    startRecording,
    stopRecording,
    replayRecording,
    stopReplay,
  } = useComputerStream();

  const { kitOnline, permissions, enableFocusCapture, refresh: refreshKit } = useKit();

  const [clickMode, setClickMode] = useState(false);
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const [typeText, setTypeText] = useState("");
  const [focusMode, setFocusMode] = useState(false);

  const handleCanvasClick = useCallback(
    (x: number, y: number) => {
      if (copycatBlocked) return;
      if (clickMode) {
        mouseClick(x, y);
      }
    },
    [clickMode, mouseClick, copycatBlocked]
  );

  useEffect(() => {
    if (copycatBlocked) {
      setClickMode(false);
      setKeyboardOpen(false);
    }
  }, [copycatBlocked]);

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

  const shellClass = embedded
    ? "absolute inset-0 z-40 overflow-hidden flex flex-col"
    : "relative w-full h-screen overflow-hidden flex flex-col";

  const Shell = embedded ? motion.div : "div";
  const shellProps = embedded
    ? {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: overlayFade,
      }
    : {};

  const ScreenShell = embedded ? motion.div : "div";
  const screenProps = embedded
    ? {
        initial: { opacity: 0, y: 28, scale: 0.98 },
        animate: { opacity: 1, y: 0, scale: 1 },
        exit: { opacity: 0, y: 20, scale: 0.99 },
        transition: modeSpringSoft,
        className: "flex-1 relative bg-black",
      }
    : { className: "flex-1 relative" };

  return (
    <Shell className={shellClass} {...shellProps}>
      <ScreenShell {...screenProps}>
        <ScreenViewer
          frame={currentFrame}
          onCanvasClick={handleCanvasClick}
          inputBlocked={copycatBlocked}
        />

        {copycatBlocked && (
          <div className="absolute top-0 left-0 right-0 z-[60] flex justify-center pointer-events-none">
            <div className="mt-4 flex items-center gap-3 bg-error text-on-error px-5 py-3 rounded-2xl shadow-lg border border-error/80 pointer-events-auto">
              <AlertTriangle size={20} className="shrink-0" />
              <div>
                <p className="text-sm font-bold tracking-wide">CopyCat is running</p>
                <p className="text-xs opacity-90">
                  {copycatMessage || "Mouse and keyboard are disabled for your safety"}
                </p>
              </div>
              <button
                type="button"
                onClick={stopReplay}
                className="ml-2 flex items-center gap-1 px-3 py-1.5 rounded-full bg-on-error/15 hover:bg-on-error/25 text-xs font-medium"
              >
                <Square size={12} fill="currentColor" />
                Stop
              </button>
            </div>
          </div>
        )}

        {copycatBlocked && (
          <div className="absolute inset-0 z-[55] bg-error/10 pointer-events-auto cursor-not-allowed" aria-hidden />
        )}

        {error && (
          <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-error text-on-error px-4 py-2 rounded-full shadow-lg z-50 flex items-center gap-2">
            <Zap size={16} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        {permissions && permissions.ready === false && (
          <div className="absolute top-6 right-4 max-w-sm bg-surface-container-high border border-outline-variant/50 rounded-2xl p-3 z-50 text-xs text-on-surface-variant shadow-lg">
            <p className="font-medium text-on-surface mb-1">Kit permissions needed</p>
            <ul className="list-disc pl-4 space-y-0.5">
              {(permissions.hints || []).slice(0, 3).map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          </div>
        )}

        {currentFrame?.fps != null && streaming && (
          <div className="absolute top-4 left-4 px-2 py-1 rounded-full bg-black/60 text-white text-[10px] font-mono z-50">
            {currentFrame.fps} fps · {currentFrame.latency_ms ?? "—"}ms · {currentFrame.backend ?? "kit"}
          </div>
        )}
      </ScreenShell>

      {/* Keyboard input popover */}
      <AnimatePresence>
        {keyboardOpen && !copycatBlocked && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={modeSpring}
            className="fixed bottom-20 left-0 right-0 z-50 flex justify-center w-full px-4 pointer-events-none"
          >
            <div className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 rounded-3xl p-3 shadow-md flex gap-2 pointer-events-auto">
            <input
              value={typeText}
              onChange={(e) => setTypeText(e.target.value)}
              placeholder="Type text to send…"
              autoFocus
              className="flex-1 px-3 py-2 text-sm rounded bg-surface-container-highest focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-on-surface-variant/50 border-0"
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
          </motion.div>
        )}
      </AnimatePresence>

      <KitToolbar
        connected={connected}
        streaming={streaming}
        clickMode={clickMode}
        keyboardOpen={keyboardOpen}
        isRecording={isRecording}
        isReplaying={isReplaying}
        copycatBlocked={copycatBlocked}
        kitOnline={kitOnline}
        permissions={permissions}
        focusMode={focusMode}
        onChat={handleChatClick}
        onConnect={connect}
        onDisconnect={disconnect}
        onStreamToggle={() => (streaming ? stopStream() : startStream({ focus_mode: focusMode }))}
        onClickModeToggle={() => setClickMode((v) => !v)}
        onScreenshot={takeScreenshot}
        onKeyboardToggle={() => setKeyboardOpen((v) => !v)}
        onRecordToggle={() => (isRecording ? stopRecording() : startRecording())}
        onReplay={() => replayRecording()}
        onFocusToggle={async () => {
          const next = !focusMode;
          setFocusMode(next);
          configureStream({ focus_mode: next });
          if (next) await enableFocusCapture();
        }}
        onPermissions={refreshKit}
      />
    </Shell>
  );
}
