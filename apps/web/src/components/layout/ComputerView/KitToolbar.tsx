import React from "react";
import { motion } from "framer-motion";
import {
  Camera,
  Circle,
  Focus,
  Keyboard,
  MessageSquare,
  Monitor,
  MousePointer2,
  Play,
  RotateCcw,
  Shield,
  ShieldAlert,
  Square,
  Wifi,
  WifiOff,
} from "lucide-react";
import { BOTTOM_BAR_LAYOUT_ID, modeSpring } from "../../../lib/motion";
import type { KitPermissions } from "../../../hooks/useKit";

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

export interface KitToolbarProps {
  connected: boolean;
  streaming: boolean;
  clickMode: boolean;
  keyboardOpen: boolean;
  isRecording: boolean;
  isReplaying: boolean;
  copycatBlocked?: boolean;
  kitOnline: boolean;
  permissions: KitPermissions | null;
  focusMode: boolean;
  onChat: () => void;
  onConnect: () => void;
  onDisconnect: () => void;
  onStreamToggle: () => void;
  onClickModeToggle: () => void;
  onScreenshot: () => void;
  onKeyboardToggle: () => void;
  onRecordToggle: () => void;
  onReplay: () => void;
  onFocusToggle: () => void;
  onPermissions?: () => void;
}

export function KitToolbar({
  connected,
  streaming,
  clickMode,
  keyboardOpen,
  isRecording,
  isReplaying,
  copycatBlocked = false,
  kitOnline,
  permissions,
  focusMode,
  onChat,
  onConnect,
  onDisconnect,
  onStreamToggle,
  onClickModeToggle,
  onScreenshot,
  onKeyboardToggle,
  onRecordToggle,
  onReplay,
  onFocusToggle,
  onPermissions,
}: KitToolbarProps) {
  const permsOk = permissions?.ready !== false;
  const PermIcon = permsOk ? Shield : ShieldAlert;

  return (
    <div className="fixed bottom-6 left-0 right-0 z-50 flex justify-center w-full px-4 pointer-events-none">
      <motion.div
        layoutId={BOTTOM_BAR_LAYOUT_ID}
        initial={{ opacity: 0, y: 14, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.92 }}
        transition={modeSpring}
        className="glass-gradient-panel border border-outline-variant/40 inline-flex items-center justify-center gap-0.5 rounded-full px-1.5 py-1 shadow-md pointer-events-auto"
      >
        <ToolbarButton onClick={onChat} label="Back to chat">
          <MessageSquare size={16} />
        </ToolbarButton>

        <ToolbarButton
          onClick={kitOnline ? onDisconnect : onConnect}
          active={connected || kitOnline}
          label={connected ? "Disconnect" : kitOnline ? "Kit online" : "Connect stream"}
        >
          {connected || kitOnline ? <Wifi size={16} /> : <WifiOff size={16} />}
        </ToolbarButton>

        <ToolbarButton
          onClick={onStreamToggle}
          active={streaming}
          disabled={!connected}
          label={streaming ? "Stop adaptive stream" : "Adaptive live stream"}
        >
          {streaming ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
        </ToolbarButton>

        <ToolbarButton
          onClick={onClickModeToggle}
          active={clickMode}
          disabled={copycatBlocked}
          label={copycatBlocked ? "CopyCat running — click disabled" : "Click mode"}
        >
          <MousePointer2 size={16} />
        </ToolbarButton>

        <ToolbarButton onClick={onScreenshot} label="Screenshot">
          <Camera size={16} />
        </ToolbarButton>

        <ToolbarButton onClick={onFocusToggle} active={focusMode} label="Focus window capture">
          <Focus size={16} />
        </ToolbarButton>

        <ToolbarButton
          onClick={onKeyboardToggle}
          active={keyboardOpen}
          disabled={copycatBlocked}
          label={copycatBlocked ? "CopyCat running — keyboard disabled" : "Keyboard input"}
        >
          <Keyboard size={16} />
        </ToolbarButton>

        <ToolbarButton
          onClick={onRecordToggle}
          active={isRecording}
          danger={isRecording}
          label={isRecording ? "Stop CopyCat recording" : "Record macro"}
        >
          <Circle size={16} fill={isRecording ? "currentColor" : "none"} />
        </ToolbarButton>

        <ToolbarButton onClick={onReplay} disabled={isReplaying} active={isReplaying} label="Replay macro">
          <RotateCcw size={16} className={isReplaying ? "animate-spin" : ""} />
        </ToolbarButton>

        <ToolbarButton
          onClick={onPermissions ?? (() => {})}
          active={!permsOk}
          label={
            permissions?.hints?.[0] ||
            (permissions?.backend === "rust" ? "Rust backend · permissions OK" : "Kit permissions")
          }
        >
          <PermIcon size={16} className={permsOk ? "text-primary" : "text-error"} />
        </ToolbarButton>

        {kitOnline && (
          <span className="ml-1 px-2 py-0.5 text-[10px] font-medium rounded-full bg-primary/15 text-primary flex items-center gap-1">
            <Monitor size={10} />
            KIT
          </span>
        )}
      </motion.div>
    </div>
  );
}
