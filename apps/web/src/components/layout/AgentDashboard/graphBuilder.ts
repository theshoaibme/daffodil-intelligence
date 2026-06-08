import type { Edge, Node } from "@xyflow/react";
import type { Agent } from "../../../hooks/useAgents";
import type { SavedPositions } from "./layoutStorage";

export const ROOT_NODE_ID = "daffodil-intelligence";

const CATEGORY_ORDER = [
  "orchestration",
  "computer",
  "productivity",
  "university",
  "ai",
  "general",
];

const CATEGORY_LABELS: Record<string, string> = {
  orchestration: "Orchestration",
  computer: "Computer",
  productivity: "Productivity",
  university: "University",
  ai: "AI",
  general: "General",
};

function defaultCategoryX(index: number, total: number): number {
  const span = Math.max(total - 1, 1) * 240;
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

  const categories = [
    ...CATEGORY_ORDER.filter((c) => grouped[c]?.length),
    ...Object.keys(grouped).filter((c) => !CATEGORY_ORDER.includes(c)),
  ];

  const pos = (id: string, x: number, y: number) => saved[id] ?? { x, y };

  const nodes: Node[] = [
    {
      id: ROOT_NODE_ID,
      type: "root",
      position: pos(ROOT_NODE_ID, 480, 40),
      data: { label: "Daffodil Intelligence" },
      draggable: true,
    },
  ];

  const edges: Edge[] = [];

  categories.forEach((category, catIndex) => {
    const catId = `cat-${category}`;
    const catX = defaultCategoryX(catIndex, categories.length);
    nodes.push({
      id: catId,
      type: "category",
      position: pos(catId, catX, 220),
      data: { label: CATEGORY_LABELS[category] ?? category, category },
      draggable: true,
    });

    const rootToCatActive =
      activeAgentId !== null &&
      grouped[category].some((a) => a.id === activeAgentId);

    edges.push({
      id: `e-${ROOT_NODE_ID}-${catId}`,
      source: ROOT_NODE_ID,
      target: catId,
      type: "activeBeam",
      data: { active: rootToCatActive },
    });

    const list = grouped[category];
    const agentSpan = Math.max(list.length - 1, 0) * 200;
    const startX = catX - agentSpan / 2;

    list.forEach((agent, agentIndex) => {
      const isActive =
        activeAgentId === agent.id ||
        agent.status === "executing" ||
        agent.status === "thinking";

      nodes.push({
        id: agent.id,
        type: "agent",
        position: pos(agent.id, startX + agentIndex * 200, 420),
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
