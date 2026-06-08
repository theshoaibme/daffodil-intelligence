import type { Edge, Node } from "@xyflow/react";
import type { Agent } from "../../../hooks/useAgents";
import { CATEGORY_LABELS } from "./agentConstants";
import { DASHBOARD_MODELS, modelNodeId } from "../../../lib/models";
import {
  ROOT_DEFAULT_X,
  ROOT_DEFAULT_Y,
  INPUT_NODE_X,
  OUTPUT_NODE_X,
  modelNodeX,
  modelNodeY,
  sideNodeY,
} from "./flowLayout";
import type { SavedPositions } from "./layoutStorage";

export const ROOT_NODE_ID = "daffodil-intelligence";

export const ROOT_INPUT_HANDLE = "input";
export const ROOT_OUTPUT_HANDLE = "output";

export const INPUT_INTEGRATIONS = [
  { id: "input-telegram", label: "Telegram", integration: "telegram" },
  { id: "input-chat", label: "Chat", integration: "chat" },
] as const;

export const OUTPUT_INTEGRATIONS = [
  { id: "output-response", label: "Response", integration: "response" },
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

export interface SimulationOverlay {
  activeAgentIds: string[];
  activeInputId?: string | null;
  modelActive?: boolean;
  activeModelId?: string | null;
  engine?: string;
}

export function buildAgentGraph(
  agents: Agent[],
  saved: SavedPositions,
  simulation: SimulationOverlay
): { nodes: Node[]; edges: Edge[] } {
  const { activeAgentIds, activeInputId = null, modelActive = false, activeModelId = null, engine } =
    simulation;
  const activeSet = new Set(activeAgentIds);
  const orchestratorActive = modelActive || activeSet.size > 0;
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
  const rootPosition = pos(ROOT_NODE_ID, ROOT_DEFAULT_X, ROOT_DEFAULT_Y);
  const rootX = rootPosition.x;
  const rootY = rootPosition.y;
  const modelCount = DASHBOARD_MODELS.length;

  const nodes: Node[] = [
    {
      id: ROOT_NODE_ID,
      type: "root",
      position: rootPosition,
      data: {
        label: "Daffodil Intelligence",
        inputs: [ROOT_INPUT_HANDLE],
        modelInputs: DASHBOARD_MODELS.map((model) => modelNodeId(model.id)),
        outputHandle: ROOT_OUTPUT_HANDLE,
        outputs: [...CATEGORY_ORDER],
        working: orchestratorActive,
      },
      draggable: true,
    },
  ];

  const edges: Edge[] = [];

  DASHBOARD_MODELS.forEach((model, index) => {
    const nodeId = modelNodeId(model.id);
    const isActive = modelActive && (activeModelId === model.id || (!activeModelId && index === 0));

    nodes.unshift({
      id: nodeId,
      type: "model",
      position: pos(nodeId, modelNodeX(index, modelCount, rootX), modelNodeY(rootY)),
      data: {
        label: model.name,
        modelName: model.name,
        provider: model.provider,
        engine: engine ?? "antigravity",
        working: isActive,
      },
      draggable: true,
    });

    edges.push({
      id: `e-${nodeId}-${ROOT_NODE_ID}`,
      source: nodeId,
      target: ROOT_NODE_ID,
      targetHandle: nodeId,
      type: "activeBeam",
      data: { active: isActive },
    });
  });

  INPUT_INTEGRATIONS.forEach((input, index) => {
    nodes.push({
      id: input.id,
      type: "integration",
      position: pos(
        input.id,
        INPUT_NODE_X,
        sideNodeY(index, INPUT_INTEGRATIONS.length, rootY)
      ),
      data: {
        label: input.label,
        integration: input.integration,
        working: orchestratorActive && activeInputId === input.id,
      },
      draggable: true,
    });

    edges.push({
      id: `e-${input.id}-${ROOT_NODE_ID}`,
      source: input.id,
      target: ROOT_NODE_ID,
      targetHandle: ROOT_INPUT_HANDLE,
      type: "activeBeam",
      data: { active: orchestratorActive && activeInputId === input.id },
    });
  });

  OUTPUT_INTEGRATIONS.forEach((output, index) => {
    const responseActive = orchestratorActive && activeSet.size > 0;

    nodes.push({
      id: output.id,
      type: "response",
      position: pos(
        output.id,
        OUTPUT_NODE_X,
        sideNodeY(index, OUTPUT_INTEGRATIONS.length, rootY)
      ),
      data: {
        label: output.label,
        integration: output.integration,
        working: responseActive,
      },
      draggable: true,
    });

    edges.push({
      id: `e-${ROOT_NODE_ID}-${output.id}`,
      source: ROOT_NODE_ID,
      sourceHandle: ROOT_OUTPUT_HANDLE,
      target: output.id,
      type: "activeBeam",
      data: { active: responseActive },
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
    const rootToCatActive = list.some((a) => activeSet.has(a.id));

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
        activeSet.has(agent.id) ||
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
