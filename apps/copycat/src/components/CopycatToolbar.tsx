import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  Circle,
  Play,
  RotateCcw,
  Shield,
  ShieldAlert,
  Square,
  MousePointerClick,
  List,
  X,
  Copy,
  Trash2,
  Monitor,
  Focus,
  MessageSquare,
} from "lucide-react";
import { BOTTOM_BAR_LAYOUT_ID, modeSpring } from "@lib";
import type { KitPermissions } from "@hooks";

interface ElectronAPI {
  isElectron?: boolean;
  closeApp?: () => void;
  setIgnoreMouse?: (ignore: boolean) => void;
  getSources?: () => Promise<Array<{ id: string; name: string; thumbnail: string }>>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

interface RecordingItem {
  id: string;
  name: string;
  source: string;
  timestamp: number;
}

// ─── ToolbarButton (internal) ────────────────────────────────────────────────

function ToolbarButton({
  onClick,
  active,
  disabled,
  danger,
  label,
  children,
  pulse,
}: {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  danger?: boolean;
  label: string;
  children: React.ReactNode;
  pulse?: boolean;
}) {
  return (
    <div className="relative group flex items-center justify-center z-[100]">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        aria-label={label}
        className={`relative w-8 h-8 flex items-center justify-center rounded-full transition-all disabled:opacity-40 z-10 ${
          active
            ? danger
              ? "bg-error text-on-error hover:bg-error/90"
              : "bg-primary text-on-primary"
            : danger
              ? "text-error hover:bg-error/15"
              : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
        }`}
      >
        {children}
        {pulse && (
          <span className="absolute top-0 right-0 w-2 h-2 rounded-full bg-error animate-pulse z-20" />
        )}
      </button>
      {/* Custom Tooltip */}
      <span className="absolute right-10 scale-95 opacity-0 pointer-events-none group-hover:scale-100 group-hover:opacity-100 transition-all duration-150 ease-out origin-right bg-neutral-900 text-neutral-100 text-[11px] font-medium px-2.5 py-1 rounded-md whitespace-nowrap shadow-lg z-[9999] border border-white/5">
        {label}
      </span>
    </div>
  );
}

// ─── GroupDivider ────────────────────────────────────────────────────────────

function GroupDivider() {
  return (
    <div className="flex items-center justify-center py-0.5 w-full">
      <div className="w-5 h-px bg-outline-variant/40 rounded-full" />
    </div>
  );
}

// ─── Main CopycatToolbar ─────────────────────────────────────────────────────

export interface CopycatToolbarProps {
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
  onStreamToggle: () => void;
  onClickModeToggle: () => void;
  onKeyboardToggle: () => void;
  onRecordToggle: () => void;
  onReplay: (name?: string) => void;
  onFocusToggle: () => void;
  onPermissions?: () => void;
  onOpenRecordings?: () => void;
  onClose?: () => void;
  onChat?: () => void;
}

export function CopycatToolbar({
  connected,
  streaming,
  clickMode,
  isRecording,
  isReplaying,
  copycatBlocked = false,
  permissions,
  onStreamToggle,
  onClickModeToggle,
  onRecordToggle,
  onReplay,
  onClose,
  onChat,
}: CopycatToolbarProps) {
  const permsOk = permissions?.ready !== false;
  const PermIcon = permsOk ? Shield : ShieldAlert;

  const isElectron = typeof window !== "undefined" && !!window.electronAPI?.isElectron;

  // Modals & LocalStorage state
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [showListModal, setShowListModal] = useState(false);
  const [showPermsModal, setShowPermsModal] = useState(false);
  
  const [tempSource, setTempSource] = useState<string>("Full Screen");
  const [tempName, setTempName] = useState<string>("");
  const [recordings, setRecordings] = useState<RecordingItem[]>(() => {
    try {
      const stored = localStorage.getItem("copycat_recordings");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  const [sources, setSources] = useState<Array<{ id: string; name: string; thumbnail: string }>>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string>("screen:0");
  
  // Dev Mode Permissions toggles
  const [screenPerm, setScreenPerm] = useState(true);
  const [controlPerm, setControlPerm] = useState(true);
  const [accessPerm, setAccessPerm] = useState(true);

  const [toast, setToast] = useState<string | null>(null);

  const anyModalOpen = showSourceModal || showListModal || showPermsModal;

  // Query window and screen sources when recording modal opens
  useEffect(() => {
    if (showSourceModal) {
      if (isElectron) {
        window.electronAPI?.getSources?.().then((res) => {
          setSources(res || []);
          if (res && res.length > 0) {
            const initialSrc = tempSource === "Full Screen" 
              ? (res.find(src => src.id.startsWith("screen:")) || res[0])
              : (res.find(src => src.id.startsWith("window:")) || res[0]);
            setSelectedSourceId(initialSrc.id);
          }
        });
      } else {
        const mock = [
          { id: "screen:0", name: "Display 1 (Full Screen)", thumbnail: "" },
          { id: "window:1", name: "Chrome - daffodil-intelligence", thumbnail: "" },
          { id: "window:2", name: "Visual Studio Code - CopycatToolbar.tsx", thumbnail: "" },
          { id: "window:3", name: "Slack - Workspace", thumbnail: "" },
          { id: "window:4", name: "PowerShell - pnpm dev", thumbnail: "" },
        ];
        setSources(mock);
        const initialSrc = tempSource === "Full Screen" 
          ? mock[0]
          : mock[1];
        setSelectedSourceId(initialSrc.id);
      }
    }
  }, [showSourceModal, isElectron, tempSource]);

  // Handle source automatic selection when toggle changes
  useEffect(() => {
    if (sources.length > 0) {
      if (tempSource === "Full Screen") {
        const screenSrc = sources.find(src => src.id.startsWith("screen:")) || sources[0];
        setSelectedSourceId(screenSrc.id);
      } else {
        const winSrc = sources.find(src => src.id.startsWith("window:")) || sources[0];
        setSelectedSourceId(winSrc.id);
      }
    }
  }, [tempSource, sources]);

  // Automatically handle Electron click-through based on modal visibility
  useEffect(() => {
    if (isElectron) {
      if (anyModalOpen) {
        window.electronAPI?.setIgnoreMouse?.(false);
      } else {
        window.electronAPI?.setIgnoreMouse?.(true);
      }
    }
  }, [anyModalOpen, isElectron]);

  const triggerToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  // Sync recordings count when opening recordings list
  const openRecordingsList = () => {
    try {
      const stored = localStorage.getItem("copycat_recordings");
      if (stored) {
        setRecordings(JSON.parse(stored));
      }
    } catch (e) {
      console.error(e);
    }
    setShowListModal(true);
  };

  // Track isRecording to handle saving macro metadata to localStorage on stop
  const prevRecordingRef = useRef(isRecording);
  useEffect(() => {
    if (prevRecordingRef.current && !isRecording) {
      const list = JSON.parse(localStorage.getItem("copycat_recordings") || "[]");
      const newId = Math.random().toString(36).substring(2, 7).toUpperCase();
      const newRec: RecordingItem = {
        id: newId,
        name: tempName.trim() || `Recording ${list.length + 1}`,
        source: tempSource,
        timestamp: Date.now(),
      };
      const updatedList = [newRec, ...list];
      localStorage.setItem("copycat_recordings", JSON.stringify(updatedList));
      setRecordings(updatedList);
      navigator.clipboard.writeText(newId).catch(console.error);
      triggerToast(`Saved! Macro ID "${newId}" copied.`);
    }
    prevRecordingRef.current = isRecording;
  }, [isRecording, tempName, tempSource]);

  return (
    <div
      className={
        isElectron
          ? "flex items-center justify-end w-full h-full pointer-events-none z-[9999] pr-6"
          : "fixed right-6 top-1/2 -translate-y-1/2 z-[9999] flex items-center h-fit pointer-events-none"
      }
    >
      <motion.div
        layoutId={BOTTOM_BAR_LAYOUT_ID}
        initial={{ opacity: 0, x: 14, scale: 0.9 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 10, scale: 0.92 }}
        transition={modeSpring}
        onMouseEnter={() => {
          if (isElectron) {
            window.electronAPI?.setIgnoreMouse?.(false);
          }
        }}
        onMouseLeave={() => {
          if (isElectron && !anyModalOpen) {
            window.electronAPI?.setIgnoreMouse?.(true);
          }
        }}
        className="backdrop-blur-xl border border-outline-variant/40 flex flex-col items-center justify-center gap-1 rounded-full px-1.5 py-3 shadow-md pointer-events-auto z-10"
        style={{
          backgroundColor: "color-mix(in srgb, var(--color-surface-container) 85%, transparent)",
        }}
      >
        {/* ── Chat redirect button ─────────────────────────────────── */}
        {onChat && (
          <ToolbarButton
            onClick={onChat}
            label="Focus session chat"
          >
            <MessageSquare size={16} />
          </ToolbarButton>
        )}

        {onChat && <GroupDivider />}

        {/* ── Play/Pause adaptive live stream ───────────────────────── */}
        <ToolbarButton
          onClick={onStreamToggle}
          active={streaming}
          disabled={!connected}
          label={
            streaming ? "Stop adaptive stream" : "Start adaptive live stream"
          }
        >
          {streaming ? (
            <Square size={16} fill="currentColor" />
          ) : (
            <Play size={16} fill="currentColor" />
          )}
        </ToolbarButton>

        <GroupDivider />

        {/* ── Click Mode (Mouse) ────────────────────────────────────── */}
        <ToolbarButton
          onClick={onClickModeToggle}
          active={clickMode}
          disabled={copycatBlocked}
          label={
            copycatBlocked
              ? "CopyCat running — click disabled"
              : clickMode
                ? "Disable click mode"
                : "Enable click mode"
          }
        >
          <MousePointerClick size={16} />
        </ToolbarButton>

        <GroupDivider />

        {/* ── Recording (Circle) ────────────────────────────────────── */}
        <ToolbarButton
          onClick={() => {
            if (isRecording) {
              onRecordToggle();
            } else {
              setTempName(`Recording ${recordings.length + 1}`);
              setShowSourceModal(true);
            }
          }}
          active={isRecording}
          danger={isRecording}
          label={isRecording ? "Stop recording" : "Start CopyCat recording"}
          pulse={isRecording}
        >
          <Circle size={16} fill={isRecording ? "currentColor" : "none"} />
        </ToolbarButton>

        {/* ── Replay last macro (Ccw) ───────────────────────────────── */}
        <ToolbarButton
          onClick={() => onReplay()}
          disabled={isReplaying}
          active={isReplaying}
          label="Replay last macro"
        >
          <RotateCcw
            size={16}
            className={isReplaying ? "animate-spin" : ""}
          />
        </ToolbarButton>

        {/* ── Recordings List (List) ────────────────────────────────── */}
        <ToolbarButton onClick={openRecordingsList} label={`View saved recordings (${recordings.length})`}>
          <List size={16} />
        </ToolbarButton>

        <GroupDivider />

        {/* ── Permissions Dialog (Shield) ───────────────────────────── */}
        <ToolbarButton
          onClick={() => {
            setShowPermsModal(true);
          }}
          active={!permsOk}
          label="System Permissions"
        >
          <PermIcon
            size={16}
            className={permsOk ? "text-primary" : "text-error"}
          />
        </ToolbarButton>

        {/* ── Close Button ─────────────────────────────────────────── */}
        {(isElectron || onClose) && (
          <>
            <GroupDivider />
            <ToolbarButton
              onClick={() => {
                if (isElectron) {
                  window.electronAPI?.closeApp?.();
                }
                onClose?.();
              }}
              danger
              label="Close CopyCat"
            >
              <X size={16} />
            </ToolbarButton>
          </>
        )}
      </motion.div>

      {/* ── MODAL DIALOGS ────────────────────────────────────────────── */}

      {/* 1. Source Selection Modal */}
      {showSourceModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm pointer-events-auto z-[99999]">
          <div 
            className="border border-outline-variant/60 rounded-3xl p-6 w-[450px] shadow-2xl flex flex-col gap-4 text-on-surface transition-all duration-200"
            style={{ backgroundColor: "var(--color-surface-container-lowest)" }}
          >
            <div className="flex justify-between items-center border-b border-outline-variant/30 pb-3">
              <h3 className="font-semibold text-base">Start Recording</h3>
              <button 
                onClick={() => { 
                  setShowSourceModal(false); 
                }} 
                className="text-on-surface-variant hover:text-on-surface p-1 rounded-full hover:bg-surface-container"
              >
                <X size={18} />
              </button>
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-on-surface-variant">Recording Name</label>
              <input 
                type="text" 
                value={tempName} 
                onChange={(e) => setTempName(e.target.value)}
                placeholder="e.g. My Macro"
                className="px-3.5 py-2.5 text-sm rounded-2xl bg-surface-container border border-outline-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/50 text-on-surface"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-on-surface-variant">Select Source</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setTempSource("Full Screen")}
                  className={`flex flex-col items-center gap-2 p-3.5 rounded-2xl border transition-all ${
                    tempSource === "Full Screen"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-outline-variant/40 bg-surface-container hover:bg-surface-container-high text-on-surface-variant"
                  }`}
                >
                  <Monitor size={22} />
                  <span className="text-xs font-semibold">Full Screen</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTempSource("Specific Window")}
                  className={`flex flex-col items-center gap-2 p-3.5 rounded-2xl border transition-all ${
                    tempSource === "Specific Window"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-outline-variant/40 bg-surface-container hover:bg-surface-container-high text-on-surface-variant"
                  }`}
                >
                  <Focus size={22} />
                  <span className="text-xs font-semibold">Specific Window</span>
                </button>
              </div>
            </div>

            {/* open window sources list */}
            {tempSource === "Specific Window" && (
              <div className="flex flex-col gap-1.5 mt-1">
                <label className="text-xs font-semibold text-on-surface-variant">Choose Application Window</label>
                <div className="grid grid-cols-2 gap-2 max-h-[160px] overflow-y-auto pr-1 custom-scrollbar">
                  {sources
                    .filter((src) => src.id.startsWith("window:") || !src.id.startsWith("screen:"))
                    .map((src) => (
                      <div
                        key={src.id}
                      onClick={() => setSelectedSourceId(src.id)}
                      className={`flex flex-col gap-1.5 p-2 rounded-2xl border cursor-pointer transition-all hover:bg-surface-container-high ${
                        selectedSourceId === src.id
                          ? "border-primary bg-primary/5 shadow-sm"
                          : "border-outline-variant/20 bg-surface-container-low"
                      }`}
                    >
                      {src.thumbnail ? (
                        <img 
                          src={src.thumbnail} 
                          alt={src.name} 
                          className="w-full h-[65px] object-cover rounded-xl border border-outline-variant/10"
                        />
                      ) : (
                        <div className="w-full h-[65px] bg-surface-container-highest/80 flex items-center justify-center rounded-xl border border-outline-variant/15 text-on-surface-variant/40">
                          <Focus size={20} />
                        </div>
                      )}
                      <span className="text-[10px] font-medium truncate px-1 text-center" title={src.name}>
                        {src.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2.5 mt-2 border-t border-outline-variant/20 pt-3">
              <button
                type="button"
                onClick={() => { 
                  setShowSourceModal(false); 
                }}
                className="flex-1 py-3 px-4 rounded-full border border-outline-variant text-sm font-medium hover:bg-surface-container transition-all"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowSourceModal(false);
                  onRecordToggle();
                }}
                className="flex-1 py-3 px-4 rounded-full bg-primary text-on-primary text-sm font-semibold hover:bg-primary/90 transition-all shadow-md"
              >
                Start
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Saved Recordings List Modal */}
      {showListModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm pointer-events-auto z-[99999]">
          <div 
            className="border border-outline-variant/60 rounded-3xl p-6 w-[440px] max-h-[80vh] shadow-2xl flex flex-col gap-4 text-on-surface overflow-hidden"
            style={{ backgroundColor: "var(--color-surface-container-lowest)" }}
          >
            <div className="flex justify-between items-center border-b border-outline-variant/30 pb-3">
              <h3 className="font-semibold text-base flex items-center gap-2">
                <List size={18} className="text-primary" />
                Saved Recordings ({recordings.length})
              </h3>
              <button 
                onClick={() => { 
                  setShowListModal(false); 
                }} 
                className="text-on-surface-variant hover:text-on-surface p-1 rounded-full hover:bg-surface-container"
              >
                <X size={18} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2 custom-scrollbar">
              {recordings.length === 0 ? (
                <div className="text-center py-8 text-on-surface-variant/65 flex flex-col items-center gap-2">
                  <Circle size={36} className="opacity-40" />
                  <p className="text-sm font-medium">No recordings found</p>
                  <p className="text-xs">Start recording macros to see them here.</p>
                </div>
              ) : (
                recordings.map((rec) => (
                  <div key={rec.id} className="p-3.5 rounded-2xl bg-surface-container border border-outline-variant/20 flex items-center justify-between gap-3 hover:border-outline-variant/50 transition-all">
                    <div className="flex flex-col gap-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm truncate max-w-[150px]">{rec.name}</span>
                        <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[9px] font-mono font-bold select-all">
                          {rec.id}
                        </span>
                      </div>
                      <span className="text-[10px] text-on-surface-variant/80 flex items-center gap-1.5">
                        <span>{rec.source}</span>
                        <span>•</span>
                        <span>{new Date(rec.timestamp).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        onClick={() => {
                          onReplay(rec.name);
                          setShowListModal(false);
                        }}
                        className="p-2 rounded-xl bg-primary text-on-primary hover:bg-primary/90 transition-all"
                        title="Play Macro"
                      >
                        <Play size={14} fill="currentColor" />
                      </button>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(rec.id).catch(console.error);
                          triggerToast("Copied ID to clipboard!");
                        }}
                        className="p-2 rounded-xl bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all border border-outline-variant/30"
                        title="Copy ID"
                      >
                        <Copy size={14} />
                      </button>
                      <button
                        onClick={() => {
                          const updated = recordings.filter(r => r.id !== rec.id);
                          setRecordings(updated);
                          localStorage.setItem("copycat_recordings", JSON.stringify(updated));
                        }}
                        className="p-2 rounded-xl bg-error/10 text-error hover:bg-error hover:text-on-error transition-all"
                        title="Delete Recording"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 3. System Permissions Modal */}
      {showPermsModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm pointer-events-auto z-[99999]">
          <div 
            className="border border-outline-variant/60 rounded-3xl p-6 w-[360px] shadow-2xl flex flex-col gap-4 text-on-surface"
            style={{ backgroundColor: "var(--color-surface-container-lowest)" }}
          >
            <div className="flex justify-between items-center border-b border-outline-variant/30 pb-3">
              <h3 className="font-semibold text-base flex items-center gap-2">
                <Shield size={18} className="text-primary" />
                System Permissions
              </h3>
              <button 
                onClick={() => { 
                  setShowPermsModal(false); 
                }} 
                className="text-on-surface-variant hover:text-on-surface p-1 rounded-full hover:bg-surface-container"
              >
                <X size={18} />
              </button>
            </div>
            
            <div className="flex flex-col gap-3 py-1">
              {/* Permission Item 1 */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-container border border-outline-variant/20">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold">Screen Capture</span>
                  <span className="text-[10px] text-on-surface-variant/75">Allow recording display content</span>
                </div>
                <button
                  type="button"
                  onClick={() => setScreenPerm(!screenPerm)}
                  className={`w-10 h-6 flex items-center rounded-full p-0.5 transition-all duration-200 ${
                    screenPerm ? "bg-primary" : "bg-outline-variant"
                  }`}
                >
                  <span className={`bg-white w-5 h-5 rounded-full shadow-md transform transition-all duration-200 ${
                    screenPerm ? "translate-x-4" : "translate-x-0"
                  }`} />
                </button>
              </div>

              {/* Permission Item 2 */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-container border border-outline-variant/20">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold">Mouse & Keyboard Control</span>
                  <span className="text-[10px] text-on-surface-variant/75">Allow sending clicks & keypresses</span>
                </div>
                <button
                  type="button"
                  onClick={() => setControlPerm(!controlPerm)}
                  className={`w-10 h-6 flex items-center rounded-full p-0.5 transition-all duration-200 ${
                    controlPerm ? "bg-primary" : "bg-outline-variant"
                  }`}
                >
                  <span className={`bg-white w-5 h-5 rounded-full shadow-md transform transition-all duration-200 ${
                    controlPerm ? "translate-x-4" : "translate-x-0"
                  }`} />
                </button>
              </div>

              {/* Permission Item 3 */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-container border border-outline-variant/20">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold">System Accessibility</span>
                  <span className="text-[10px] text-on-surface-variant/75">Windows Accessibility automation API</span>
                </div>
                <button
                  type="button"
                  onClick={() => setAccessPerm(!accessPerm)}
                  className={`w-10 h-6 flex items-center rounded-full p-0.5 transition-all duration-200 ${
                    accessPerm ? "bg-primary" : "bg-outline-variant"
                  }`}
                >
                  <span className={`bg-white w-5 h-5 rounded-full shadow-md transform transition-all duration-200 ${
                    accessPerm ? "translate-x-4" : "translate-x-0"
                  }`} />
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={() => { 
                setShowPermsModal(false); 
                triggerToast("Permissions updated successfully!");
              }}
              className="w-full py-3 rounded-full bg-primary text-on-primary text-sm font-semibold hover:bg-primary/90 transition-all shadow-md"
            >
              Save & Apply
            </button>
          </div>
        </div>
      )}

      {/* ── TOAST NOTIFICATION ───────────────────────────────────────── */}
      {toast && (
        <div className="fixed bottom-10 left-1/2 -translate-x-1/2 bg-neutral-900/95 text-neutral-100 text-xs font-medium py-2.5 px-5 rounded-full shadow-xl pointer-events-auto z-[999999] border border-white/10 flex items-center gap-2">
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}
