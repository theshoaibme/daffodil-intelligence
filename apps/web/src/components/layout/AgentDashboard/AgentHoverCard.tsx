import { useLayoutEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Agent } from "../../../hooks/useAgents";
import { AgentDetailContent, useAgentSkills } from "./agentDetailContent";

export interface HoverAnchor {
  x: number;
  y: number;
}

const CARD_WIDTH = 300;
const VIEWPORT_PAD = 12;
const OFFSET_X = 18;
const OFFSET_Y = -12;

function clampCardPosition(anchor: HoverAnchor, height: number) {
  let x = anchor.x + OFFSET_X;
  let y = anchor.y + OFFSET_Y;

  const maxX = window.innerWidth - CARD_WIDTH - VIEWPORT_PAD;
  const maxY = window.innerHeight - height - VIEWPORT_PAD;

  if (x > maxX) x = anchor.x - CARD_WIDTH - OFFSET_X;
  if (y > maxY) y = Math.max(VIEWPORT_PAD, maxY);
  if (x < VIEWPORT_PAD) x = VIEWPORT_PAD;
  if (y < VIEWPORT_PAD) y = VIEWPORT_PAD;

  return { x, y };
}

interface AgentHoverCardProps {
  agent: Agent | null;
  anchor: HoverAnchor | null;
  onPointerEnter: () => void;
  onPointerLeave: () => void;
}

export function AgentHoverCard({ agent, anchor, onPointerEnter, onPointerLeave }: AgentHoverCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const { skills, loading } = useAgentSkills(agent?.id ?? null);

  useLayoutEffect(() => {
    if (!agent || !anchor || !cardRef.current) return;
    const height = cardRef.current.offsetHeight;
    setPosition(clampCardPosition(anchor, height));
  }, [agent, anchor, skills, loading]);

  return (
    <AnimatePresence>
      {agent && anchor && (
        <motion.div
          ref={cardRef}
          key={agent.id}
          initial={{ opacity: 0, scale: 0.96, y: 4 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.98, y: 2 }}
          transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
          className="fixed z-[70] w-[300px] max-h-[min(70vh,420px)] overflow-y-auto custom-scrollbar rounded-2xl border border-outline-variant/40 bg-surface-container-lowest shadow-xl pointer-events-auto"
          style={{ left: position.x, top: position.y }}
          onMouseEnter={onPointerEnter}
          onMouseLeave={onPointerLeave}
        >
          <div className="px-4 py-4">
            <AgentDetailContent agent={agent} skills={skills} loadingSkills={loading} compact />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
