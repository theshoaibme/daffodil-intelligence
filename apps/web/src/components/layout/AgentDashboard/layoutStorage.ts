import type { Node } from "@xyflow/react";

const STORAGE_KEY = "di-agent-canvas-layout";

export type SavedPositions = Record<string, { x: number; y: number }>;

export function loadLayout(): SavedPositions {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedPositions) : {};
  } catch {
    return {};
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
