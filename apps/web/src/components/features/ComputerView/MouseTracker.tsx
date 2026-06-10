import { motion } from "framer-motion";
import { Crosshair } from "lucide-react";

export interface MousePosition {
  x: number;
  y: number;
}

export interface TrailPoint {
  x: number;
  y: number;
  t: number;
}

interface MouseTrackerProps {
  /** Current mouse position in screen coordinates */
  position: MousePosition | null;
  /** Trail of recent positions for path visualization */
  trail?: TrailPoint[];
  /** Last click position */
  lastClick?: MousePosition | null;
  /** Frame dimensions for coordinate scaling */
  frameDimensions?: { width: number; height: number } | null;
  /** Container dimensions for display scaling */
  containerRect?: DOMRect | null;
}

export function MouseTracker({
  position,
  trail = [],
  lastClick,
  frameDimensions,
  containerRect,
}: MouseTrackerProps) {
  if (!position || !frameDimensions || !containerRect) return null;

  const scaleX = containerRect.width / frameDimensions.width;
  const scaleY = containerRect.height / frameDimensions.height;
  const displayX = position.x * scaleX;
  const displayY = position.y * scaleY;

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 4 }}>
      {/* Mouse trail path */}
      {trail.length > 2 && (
        <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }}>
          <polyline
            points={trail
              .map((p) => `${p.x * scaleX},${p.y * scaleY}`)
              .join(" ")}
            fill="none"
            stroke="rgba(66, 89, 255, 0.25)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}

      {/* Current position indicator */}
      <motion.div
        className="absolute"
        animate={{ left: displayX, top: displayY }}
        transition={{ type: "spring", stiffness: 500, damping: 35, mass: 0.5 }}
        style={{ transform: "translate(-50%, -50%)", zIndex: 3 }}
      >
        <Crosshair
          size={18}
          className="text-primary/70"
          strokeWidth={1.5}
        />
      </motion.div>

      {/* Coordinate badge */}
      <motion.div
        className="absolute"
        animate={{ left: displayX + 16, top: displayY - 12 }}
        transition={{ type: "spring", stiffness: 500, damping: 35, mass: 0.5 }}
        style={{ zIndex: 3 }}
      >
        <div className="px-1.5 py-0.5 rounded bg-black/60 text-white text-[9px] font-mono whitespace-nowrap">
          {position.x}, {position.y}
        </div>
      </motion.div>

      {/* Last click indicator */}
      {lastClick && (
        <div
          className="absolute"
          style={{
            left: lastClick.x * scaleX,
            top: lastClick.y * scaleY,
            transform: "translate(-50%, -50%)",
            zIndex: 2,
          }}
        >
          <span className="block w-4 h-4 rounded-full bg-primary/30 border border-primary/50" />
        </div>
      )}
    </div>
  );
}
