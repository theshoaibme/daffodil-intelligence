import type { Node } from "@xyflow/react";
import type { Agent } from "@hooks";
import { computeDefaultPositions } from "./graphBuilder";
import { DEFAULT_CANVAS_LAYOUT } from "./defaultCanvasLayout";
import type { SavedPositions } from "./flowLayout";

const STORAGE_KEY = "di-agent-canvas-layout";
const DEFAULT_STORAGE_KEY = "di-agent-canvas-layout-default";

export type { SavedPositions } from "./flowLayout";

function nodesToPositions(nodes: Node[]): SavedPositions {
  const positions: SavedPositions = {};
  for (const node of nodes) {
    positions[node.id] = { x: node.position.x, y: node.position.y };
  }
  return positions;
}

function readStored(key: string): SavedPositions {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return {};
    return JSON.parse(raw) as SavedPositions;
  } catch {
    return {};
  }
}

/** Baseline layout: shipped default → optional saved default → computed fallbacks for new nodes. */
export function resolveDefaultLayout(agents: Agent[] = []): SavedPositions {
  const computed = computeDefaultPositions(agents);
  const merged: SavedPositions = { ...computed, ...DEFAULT_CANVAS_LAYOUT };

  const savedDefault = readStored(DEFAULT_STORAGE_KEY);
  Object.assign(merged, savedDefault);

  for (const agent of agents) {
    if (!merged[agent.id] && computed[agent.id]) {
      merged[agent.id] = computed[agent.id];
    }
  }

  for (const id of ["output-memory", "output-response"] as const) {
    const y =
      savedDefault[id]?.y ??
      DEFAULT_CANVAS_LAYOUT[id]?.y ??
      computed[id]?.y;
    const x =
      savedDefault[id]?.x ??
      DEFAULT_CANVAS_LAYOUT[id]?.x ??
      computed[id]?.x;
    if (x != null && y != null) merged[id] = { x, y };
  }

  return merged;
}

function migrateCustomLayoutToDefaultOnce(): void {
  if (localStorage.getItem(DEFAULT_STORAGE_KEY)) return;
  const custom = readStored(STORAGE_KEY);
  if (Object.keys(custom).length === 0) return;
  localStorage.setItem(DEFAULT_STORAGE_KEY, JSON.stringify(custom));
}

export function loadLayout(agents: Agent[] = []): SavedPositions {
  migrateCustomLayoutToDefaultOnce();
  const defaults = resolveDefaultLayout(agents);
  const custom = readStored(STORAGE_KEY);
  return { ...defaults, ...custom };
}

export function saveLayout(nodes: Node[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(nodesToPositions(nodes)));
}

/** Persist the current canvas as the default layout (used on reset). */
export function saveDefaultLayout(nodes: Node[]): void {
  localStorage.setItem(DEFAULT_STORAGE_KEY, JSON.stringify(nodesToPositions(nodes)));
}

export function clearLayout(): void {
  localStorage.removeItem(STORAGE_KEY);
}
