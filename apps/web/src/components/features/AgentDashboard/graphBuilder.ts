import type { Edge, Node } from "@xyflow/react";
import type { Agent } from "@hooks";
import { CATEGORY_LABELS } from "./agentConstants";
import { DASHBOARD_MODELS, isAgentActiveFromTools, modelNodeId } from "@lib";
import {
  ROOT_DEFAULT_X,
  ROOT_DEFAULT_Y,
  INPUT_OFFSET_X,
  OUTPUT_OFFSET_X,
  CATEGORY_ROW_OFFSET_Y,
  AGENT_ROW_OFFSET_Y,
  CATEGORY_COL_GAP,
  AGENT_COL_GAP,
  modelNodeX,
  modelNodeY,
  rightOutputNodeY,
  sideNodeY,
} from "./flowLayout";
import type { SavedPositions } from "./flowLayout";

export const ROOT_NODE_ID = "daffodil-intelligence";

export const ROOT_INPUT_HANDLE = "input";
/** Legacy single output — category agents use bottom handles. */
export const ROOT_OUTPUT_HANDLE = "output";
export const OUTPUT_MEMORY_HANDLE = "output-memory";
export const OUTPUT_RESPONSE_HANDLE = "output-response";

export const INPUT_INTEGRATIONS = [
  { id: "input-telegram", label: "Telegram", integration: "telegram" },
  { id: "input-chat", label: "Chat", integration: "chat" },
] as const;

export const OUTPUT_INTEGRATIONS = [
  { id: "output-memory", label: "Memory", integration: "memory" },
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

function defaultCategoryX(index: number, rootX: number): number {
  const span = (CATEGORY_ORDER.length - 1) * CATEGORY_COL_GAP;
  return rootX - span / 2 + index * CATEGORY_COL_GAP;
}

export interface SimulationOverlay {
  activeAgentIds: string[];
  activeInputId?: string | null;
  modelActive?: boolean;
  activeModelId?: string | null;
  engine?: string;
  memoryActive?: boolean;
  activeTools?: string[];
}

export function buildAgentGraph(
  agents: Agent[],
  saved: SavedPositions,
  simulation: SimulationOverlay
): { nodes: Node[]; edges: Edge[] } {
  const {
    activeAgentIds,
    activeInputId = null,
    modelActive = false,
    activeModelId = null,
    engine,
    memoryActive = false,
    activeTools = [],
  } = simulation;
  const activeSet = new Set(activeAgentIds);
  const orchestratorActive = modelActive || activeSet.size > 0 || memoryActive || activeTools.length > 0;
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
        sideOutputs: OUTPUT_INTEGRATIONS.map((o) => o.id),
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
        rootX - INPUT_OFFSET_X,
        sideNodeY(index, INPUT_INTEGRATIONS.length, rootY)
      ),
      data: {
        label: input.label,
        integration: input.integration,
        working:
          orchestratorActive &&
          (activeInputId === input.id ||
            (!activeInputId && input.id === "input-chat")),
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
    const isMemory = output.integration === "memory";
    const outputActive = isMemory
      ? memoryActive
      : orchestratorActive && (activeSet.size > 0 || activeTools.length > 0);

    nodes.push({
      id: output.id,
      type: isMemory ? "memory" : "response",
      position: pos(
        output.id,
        rootX + OUTPUT_OFFSET_X,
        rightOutputNodeY(index, OUTPUT_INTEGRATIONS.length, rootY)
      ),
      data: {
        label: output.label,
        integration: output.integration,
        working: outputActive,
      },
      draggable: true,
    });

    edges.push({
      id: `e-${ROOT_NODE_ID}-${output.id}`,
      source: ROOT_NODE_ID,
      sourceHandle: output.id,
      target: output.id,
      type: "activeBeam",
      data: { active: outputActive },
    });
  });

  CATEGORY_ORDER.forEach((category, catIndex) => {
    const catId = `cat-${category}`;
    const catX = defaultCategoryX(catIndex, rootX);
    nodes.push({
      id: catId,
      type: "category",
      position: pos(catId, catX, rootY + CATEGORY_ROW_OFFSET_Y),
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
    const agentSpan = Math.max(list.length - 1, 0) * AGENT_COL_GAP;
    const startX = catX - agentSpan / 2;

    list.forEach((agent, agentIndex) => {
      const isActive =
        activeSet.has(agent.id) ||
        isAgentActiveFromTools(agent.id, activeTools) ||
        agent.status === "executing" ||
        agent.status === "thinking";

      nodes.push({
        id: agent.id,
        type: "agent",
        position: pos(agent.id, startX + agentIndex * AGENT_COL_GAP, rootY + AGENT_ROW_OFFSET_Y),
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

export function computeDefaultPositions(agents: Agent[]): SavedPositions {
  const { nodes } = buildAgentGraph(agents, {}, { activeAgentIds: [] });
  const positions: SavedPositions = {};
  for (const node of nodes) {
    positions[node.id] = { x: node.position.x, y: node.position.y };
  }
  return positions;
}
