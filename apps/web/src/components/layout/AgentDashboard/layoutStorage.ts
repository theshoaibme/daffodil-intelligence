import type { Node } from "@xyflow/react";
import type { Agent } from "../../../hooks/useAgents";
import { computeDefaultPositions } from "./graphBuilder";
import type { SavedPositions } from "./flowLayout";

const STORAGE_KEY = "di-agent-canvas-layout";

export type { SavedPositions } from "./flowLayout";

export function loadLayout(agents: Agent[] = []): SavedPositions {
  const defaults = computeDefaultPositions(agents);
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const custom = raw ? (JSON.parse(raw) as SavedPositions) : {};
    return { ...defaults, ...custom };
  } catch {
    return defaults;
  }
}

export function saveLayout(nodes: Node[]): void {
  const positions: SavedPositions = {};
  for (const node of nodes) {
    positions[node.id] = { x: node.position.x, y: node.position.y };
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(positions));
}

export function clearLayout(): void {
  localStorage.removeItem(STORAGE_KEY);
}
