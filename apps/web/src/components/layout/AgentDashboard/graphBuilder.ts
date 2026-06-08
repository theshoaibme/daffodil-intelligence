import type { Edge, Node } from "@xyflow/react";
import type { Agent } from "../../../hooks/useAgents";
import { CATEGORY_LABELS } from "./agentConstants";
import {
  ROOT_DEFAULT_X,
  ROOT_DEFAULT_Y,
  INPUT_NODE_X,
  defaultInputY,
} from "./flowLayout";
import type { SavedPositions } from "./layoutStorage";

export const ROOT_NODE_ID = "daffodil-intelligence";

export const ROOT_INPUT_HANDLE = "input";

export const INPUT_INTEGRATIONS = [
  { id: "input-telegram", label: "Telegram", integration: "telegram" },
  { id: "input-chat", label: "Chat", integration: "chat" },
] as const;

export const CATEGORY_ORDER = [
  "orchestration",
  "computer",
  "productivity",
  "university",
  "ai",
  "general",
] as const;

function defaultCategoryX(index: number): number {
  const span = (CATEGORY_ORDER.length - 1) * 240;
  return 520 - span / 2 + index * 240;
}

export function buildAgentGraph(
  agents: Agent[],
  saved: SavedPositions,
  activeAgentId: string | null
): { nodes: Node[]; edges: Edge[] } {
  const grouped = agents.reduce(
    (acc, agent) => {
      const cat = agent.category || "general";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(agent);
      return acc;
    },
    {} as Record<string, Agent[]>
  );

  const pos = (id: string, x: number, y: number) => saved[id] ?? { x, y };

  const rootActive = activeAgentId !== null;

  const nodes: Node[] = [
    {
      id: ROOT_NODE_ID,
      type: "root",
      position: pos(ROOT_NODE_ID, ROOT_DEFAULT_X, ROOT_DEFAULT_Y),
      data: {
        label: "Daffodil Intelligence",
        inputs: [ROOT_INPUT_HANDLE],
        outputs: [...CATEGORY_ORDER],
        working: rootActive,
      },
      draggable: true,
    },
  ];

  const edges: Edge[] = [];

  INPUT_INTEGRATIONS.forEach((input, index) => {
    nodes.push({
      id: input.id,
      type: "integration",
      position: pos(input.id, INPUT_NODE_X, defaultInputY(index, INPUT_INTEGRATIONS.length)),
      data: { label: input.label, integration: input.integration },
      draggable: true,
    });

    edges.push({
      id: `e-${input.id}-${ROOT_NODE_ID}`,
      source: input.id,
      target: ROOT_NODE_ID,
      targetHandle: ROOT_INPUT_HANDLE,
      type: "activeBeam",
      data: { active: rootActive },
    });
  });

  CATEGORY_ORDER.forEach((category, catIndex) => {
    const catId = `cat-${category}`;
    const catX = defaultCategoryX(catIndex);
    nodes.push({
      id: catId,
      type: "category",
      position: pos(catId, catX, 240),
      data: { label: CATEGORY_LABELS[category] ?? category, category },
      draggable: true,
    });

    const list = grouped[category] ?? [];
    const rootToCatActive =
      activeAgentId !== null && list.some((a) => a.id === activeAgentId);

    edges.push({
      id: `e-${ROOT_NODE_ID}-${catId}`,
      source: ROOT_NODE_ID,
      sourceHandle: category,
      target: catId,
      type: "activeBeam",
      data: { active: rootToCatActive },
    });
    const agentSpan = Math.max(list.length - 1, 0) * 130;
    const startX = catX - agentSpan / 2;

    list.forEach((agent, agentIndex) => {
      const isActive =
        activeAgentId === agent.id ||
        agent.status === "executing" ||
        agent.status === "thinking";

      nodes.push({
        id: agent.id,
        type: "agent",
        position: pos(agent.id, startX + agentIndex * 130, 420),
        data: {
          label: agent.name,
          category: agent.category,
          status: isActive ? agent.status || "executing" : agent.status,
          working: isActive,
        },
        draggable: true,
      });

      edges.push({
        id: `e-${catId}-${agent.id}`,
        source: catId,
        target: agent.id,
        type: "activeBeam",
        data: { active: isActive },
      });
    });
  });

  return { nodes, edges };
}
