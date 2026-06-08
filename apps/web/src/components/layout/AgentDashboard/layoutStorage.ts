import type { Node } from "@xyflow/react";
import { DEFAULT_CANVAS_LAYOUT } from "./defaultLayout";

const STORAGE_KEY = "di-agent-canvas-layout";

export type SavedPositions = Record<string, { x: number; y: number }>;

export function loadLayout(): SavedPositions {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const custom = raw ? (JSON.parse(raw) as SavedPositions) : {};
    return { ...DEFAULT_CANVAS_LAYOUT, ...custom };
  } catch {
    return { ...DEFAULT_CANVAS_LAYOUT };
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
