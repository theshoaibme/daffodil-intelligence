import type { Node } from "@xyflow/react";
import type { Agent } from "@hooks";
import { computeDefaultPositions } from "./graphBuilder";
import { DEFAULT_CANVAS_LAYOUT } from "./defaultCanvasLayout";
import type { SavedPositions } from "./flowLayout";
import { fetchSimulationLayout, saveSimulationLayout } from "@lib/simulationLayoutApi";

const STORAGE_KEY = "di-agent-canvas-layout";
const DEFAULT_STORAGE_KEY = "di-agent-canvas-layout-default";

export type { SavedPositions } from "./flowLayout";

let layoutRevision = 0;
const listeners = new Set<() => void>();

function bumpRevision() {
  layoutRevision += 1;
  listeners.forEach((fn) => fn());
}

export function getLayoutRevision(): number {
  return layoutRevision;
}

export function subscribeLayoutRevision(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

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

function writeStored(key: string, positions: SavedPositions): void {
  localStorage.setItem(key, JSON.stringify(positions));
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
  writeStored(DEFAULT_STORAGE_KEY, custom);
}

export function loadLayout(agents: Agent[] = []): SavedPositions {
  migrateCustomLayoutToDefaultOnce();
  const defaults = resolveDefaultLayout(agents);
  const custom = readStored(STORAGE_KEY);
  return { ...defaults, ...custom };
}

export function saveLayout(nodes: Node[]): void {
  const positions = nodesToPositions(nodes);
  writeStored(STORAGE_KEY, positions);
  void saveSimulationLayout({ custom: positions }).catch(() => undefined);
}

/** Persist the current canvas as the default layout (used on reset). */
export function saveDefaultLayout(nodes: Node[]): void {
  const positions = nodesToPositions(nodes);
  writeStored(DEFAULT_STORAGE_KEY, positions);
  void saveSimulationLayout({ default: positions }).catch(() => undefined);
}

/** Save both custom + default to localStorage and backend (edit-mode Save). */
export function saveLayoutBundle(nodes: Node[]): void {
  const positions = nodesToPositions(nodes);
  writeStored(STORAGE_KEY, positions);
  writeStored(DEFAULT_STORAGE_KEY, positions);
  void saveSimulationLayout({ custom: positions, default: positions }).catch(() => undefined);
}

export function clearLayout(): void {
  localStorage.removeItem(STORAGE_KEY);
  void saveSimulationLayout({ custom: {} }).catch(() => undefined);
  bumpRevision();
}

/** Pull remote layout into localStorage (backend is source of truth when present). */
export async function hydrateLayoutFromBackend(): Promise<boolean> {
  const remote = await fetchSimulationLayout();
  if (!remote) return false;

  let changed = false;
  if (remote.default && Object.keys(remote.default).length > 0) {
    writeStored(DEFAULT_STORAGE_KEY, remote.default);
    changed = true;
  }
  if (remote.custom && Object.keys(remote.custom).length > 0) {
    writeStored(STORAGE_KEY, remote.custom);
    changed = true;
  } else if (remote.custom && Object.keys(remote.custom).length === 0) {
    localStorage.removeItem(STORAGE_KEY);
    changed = true;
  }

  if (changed) bumpRevision();
  return changed;
}

/** Push current localStorage layout to backend as the default snapshot. */
export async function syncLocalLayoutToBackend(): Promise<void> {
  const custom = readStored(STORAGE_KEY);
  const defaults = readStored(DEFAULT_STORAGE_KEY);
  const payload: { custom?: SavedPositions; default?: SavedPositions } = {};
  if (Object.keys(custom).length > 0) payload.custom = custom;
  if (Object.keys(defaults).length > 0) payload.default = defaults;
  if (Object.keys(payload).length === 0) return;
  await saveSimulationLayout(payload);
}
