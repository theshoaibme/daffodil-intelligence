import { ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { AudioInputDevice } from "@hooks";
import { WaveformBars } from "./WaveformBars";

interface VoiceRecordingControlsProps {
  levels: number[];
  devices: AudioInputDevice[];
  selectedDeviceId: string;
  onSelectDevice: (deviceId: string) => void;
  onStop: () => void;
}

export function VoiceRecordingControls({
  levels,
  devices,
  selectedDeviceId,
  onSelectDevice,
  onStop,
}: VoiceRecordingControlsProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  const showDeviceMenu = devices.length > 1;

  return (
    <div className="flex items-center gap-2">
      <WaveformBars levels={levels} animated />
      {showDeviceMenu && (
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Select microphone"
            className="flex h-7 w-7 items-center justify-center rounded-full text-on-surface-variant hover:text-on-surface border-0 outline-none bg-transparent cursor-pointer"
          >
            <ChevronDown size={16} />
          </button>
          {menuOpen && (
            <div className="absolute bottom-full right-0 mb-2 min-w-[12rem] glass-gradient-panel border border-outline-variant/40 rounded-2xl shadow-md z-[70] py-1 overflow-hidden">
              {devices.map((device) => (
                <button
                  key={device.deviceId}
                  type="button"
                  onClick={() => {
                    onSelectDevice(device.deviceId);
                    setMenuOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs border-0 outline-none cursor-pointer ${
                    device.deviceId === selectedDeviceId
                      ? "text-on-surface bg-surface-container-high"
                      : "text-on-surface-variant hover:bg-surface-container-high/60"
                  }`}
                >
                  {device.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      <button
        type="button"
        onClick={onStop}
        aria-label="Stop recording"
        className="w-8 h-8 flex items-center justify-center rounded-full bg-on-surface text-surface-container-lowest hover:opacity-90 border-0 outline-none cursor-pointer shadow-sm"
      >
        <span className="block w-2.5 h-2.5 rounded-[2px] bg-current" />
      </button>
    </div>
  );
}
