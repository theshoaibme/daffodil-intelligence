import React, { useRef, useEffect, useCallback, useState } from "react";
import { Monitor } from "lucide-react";

export interface MousePosition {
  x: number;
  y: number;
}

interface ScreenViewerProps {
  frame: { frame: string; width: number; height: number } | null;
  onCanvasClick: (x: number, y: number) => void;
  inputBlocked?: boolean;
  mousePosition?: MousePosition | null;
  showAgentCursor?: boolean;
}

/** Ripple marker that fades after a click */
interface ClickRipple {
  id: number;
  canvasX: number;
  canvasY: number;
}

let rippleCounter = 0;

export function ScreenViewer({
  frame,
  onCanvasClick,
  inputBlocked = false,
  mousePosition,
  showAgentCursor = false,
}: ScreenViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const [hoverCoords, setHoverCoords] = useState<{ x: number; y: number; screenX: number; screenY: number } | null>(null);
  const [clickRipples, setClickRipples] = useState<ClickRipple[]>([]);

  // Render frame to main canvas
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

  // Draw agent cursor overlay
  useEffect(() => {
    if (!overlayRef.current || !frame || !showAgentCursor || !mousePosition) return;
    const canvas = overlayRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    canvas.width = rect.width;
    canvas.height = rect.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Scale mouse coordinates to canvas display size
    const scaleX = rect.width / frame.width;
    const scaleY = rect.height / frame.height;
    const dx = mousePosition.x * scaleX;
    const dy = mousePosition.y * scaleY;

    // Outer glow ring
    ctx.beginPath();
    ctx.arc(dx, dy, 14, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(66, 89, 255, 0.5)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Inner dot
    ctx.beginPath();
    ctx.arc(dx, dy, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#4259ff";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Label
    ctx.font = "bold 10px 'Roboto Flex', sans-serif";
    ctx.fillStyle = "#4259ff";
    ctx.textAlign = "center";
    ctx.fillText("Agent", dx, dy + 24);
  }, [mousePosition, frame, showAgentCursor]);

  const toScreenCoords = useCallback(
    (clientX: number, clientY: number) => {
      if (!canvasRef.current || !frame) return null;
      const rect = canvasRef.current.getBoundingClientRect();
      const scaleX = frame.width / rect.width;
      const scaleY = frame.height / rect.height;
      return {
        x: Math.round((clientX - rect.left) * scaleX),
        y: Math.round((clientY - rect.top) * scaleY),
      };
    },
    [frame]
  );

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (inputBlocked || !frame) return;
      const coords = toScreenCoords(e.clientX, e.clientY);
      if (!coords) return;
      onCanvasClick(coords.x, coords.y);

      // Add click ripple at display position
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        const id = ++rippleCounter;
        setClickRipples((prev) => [...prev, { id, canvasX: e.clientX - rect.left, canvasY: e.clientY - rect.top }]);
        setTimeout(() => setClickRipples((prev) => prev.filter((r) => r.id !== id)), 600);
      }
    },
    [frame, onCanvasClick, inputBlocked, toScreenCoords]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!frame) return;
      const coords = toScreenCoords(e.clientX, e.clientY);
      if (coords) {
        setHoverCoords({ ...coords, screenX: e.clientX, screenY: e.clientY });
      }
    },
    [frame, toScreenCoords]
  );

  const handleMouseLeave = useCallback(() => setHoverCoords(null), []);

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
    <div className="absolute inset-0">
      {/* Main screen canvas */}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 w-full h-full object-contain bg-black ${
          inputBlocked ? "cursor-not-allowed pointer-events-none" : "cursor-crosshair"
        }`}
        style={{ imageRendering: "pixelated" }}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        title={inputBlocked ? "CopyCat is running — input disabled" : "Click to interact"}
      />

      {/* Agent cursor overlay canvas */}
      {showAgentCursor && mousePosition && (
        <canvas
          ref={overlayRef}
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ zIndex: 2 }}
        />
      )}

      {/* Click ripple effects */}
      {clickRipples.map((ripple) => (
        <span
          key={ripple.id}
          className="absolute pointer-events-none"
          style={{
            left: ripple.canvasX,
            top: ripple.canvasY,
            transform: "translate(-50%, -50%)",
            zIndex: 3,
          }}
        >
          <span className="block w-8 h-8 rounded-full border-2 border-primary animate-ping opacity-75" />
        </span>
      ))}

      {/* Coordinate tooltip on hover */}
      {hoverCoords && !inputBlocked && (
        <div
          className="absolute pointer-events-none z-10 px-2 py-0.5 rounded-full bg-black/70 text-white text-[10px] font-mono whitespace-nowrap"
          style={{
            left: Math.min(hoverCoords.screenX - (canvasRef.current?.getBoundingClientRect().left ?? 0) + 14, (canvasRef.current?.getBoundingClientRect().width ?? 200) - 80),
            top: hoverCoords.screenY - (canvasRef.current?.getBoundingClientRect().top ?? 0) - 8,
          }}
        >
          {hoverCoords.x}, {hoverCoords.y}
        </div>
      )}
    </div>
  );
}
