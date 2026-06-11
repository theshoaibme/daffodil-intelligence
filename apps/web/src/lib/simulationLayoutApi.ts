import type { SavedPositions } from "../components/features/AgentDashboard/flowLayout";
import { getAuthHeaders } from "./api";

const API_BASE = import.meta.env.VITE_API_URL || "";

function url(path: string): string {
  return `${API_BASE.replace(/\/$/, "")}${path}`;
}

export interface SimulationLayoutRemote {
  custom: SavedPositions;
  default: SavedPositions;
  updated_at?: string | null;
}

export async function fetchSimulationLayout(): Promise<SimulationLayoutRemote | null> {
  const headers = getAuthHeaders() as Record<string, string>;
  if (!headers.Authorization) return null;

  try {
    const res = await fetch(url("/api/agents/simulation-layout"), { headers });
    if (!res.ok) return null;
    return (await res.json()) as SimulationLayoutRemote;
  } catch {
    return null;
  }
}

export async function saveSimulationLayout(
  payload: Partial<Pick<SimulationLayoutRemote, "custom" | "default">>
): Promise<void> {
  const headers = getAuthHeaders() as Record<string, string>;
  if (!headers.Authorization) return;

  const res = await fetch(url("/api/agents/simulation-layout"), {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || "Failed to save simulation layout");
  }
}
