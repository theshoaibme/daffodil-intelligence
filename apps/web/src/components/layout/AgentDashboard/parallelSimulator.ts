import type { Agent } from "../../../hooks/useAgents";
import type { RuntimeStatus } from "../../../hooks/useRuntimeStatus";
import { formatModelLabel } from "../../../hooks/useRuntimeStatus";
import { DASHBOARD_MODELS } from "../../../lib/models";
import { INPUT_INTEGRATIONS } from "./graphBuilder";
import { getSimulatedModelTask, getSimulatedTask } from "./simulatorTasks";

export interface ParallelTask {
  agentId: string;
  agentName: string;
  category: string;
  task: string;
}

export interface ParallelSimulationState {
  activeAgentIds: string[];
  activeInputId: string;
  activeModelId: string;
  modelActive: boolean;
  modelTask: string;
  pipelineLabel: string;
  tasks: ParallelTask[];
}

const PARALLEL_COUNT = 3;

function inputLabel(inputId: string): string {
  return inputId === "input-chat" ? "Chat" : "Telegram";
}

function pickActiveModel(round: number, runtime?: RuntimeStatus): string {
  return DASHBOARD_MODELS[round % DASHBOARD_MODELS.length]?.id ?? runtime?.model ?? "gemini-2.0-flash";
}

export function nextParallelSimulation(
  agents: Agent[],
  round: number,
  runtime?: RuntimeStatus
): ParallelSimulationState {
  const engine = runtime?.engine ?? "antigravity";
  const activeModelId = pickActiveModel(round, runtime);
  const modelName = formatModelLabel(activeModelId);
  const activeInputId = INPUT_INTEGRATIONS[round % INPUT_INTEGRATIONS.length].id;

  const busy = agents.filter((a) => a.status === "executing" || a.status === "thinking");
  if (busy.length > 0) {
    const activeAgentIds = busy.slice(0, PARALLEL_COUNT).map((a) => a.id);
    const tasks = busy.slice(0, PARALLEL_COUNT).map((agent) => ({
      agentId: agent.id,
      agentName: agent.name,
      category: agent.category,
      task: agent.currentTask || getSimulatedTask(agent.id, agent.category),
    }));
    return {
      activeAgentIds,
      activeInputId,
      activeModelId,
      modelActive: true,
      modelTask: getSimulatedModelTask(engine),
      pipelineLabel: `${inputLabel(activeInputId)} → ${modelName} → Orchestrator → ${tasks.length} agents`,
      tasks,
    };
  }

  const grouped = agents.reduce(
    (acc, agent) => {
      const cat = agent.category || "general";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(agent);
      return acc;
    },
    {} as Record<string, Agent[]>
  );

  const categories = Object.keys(grouped).sort();
  if (categories.length === 0) {
    return {
      activeAgentIds: [],
      activeInputId,
      activeModelId,
      modelActive: false,
      modelTask: "",
      pipelineLabel: "",
      tasks: [],
    };
  }

  const activeAgentIds: string[] = [];
  const tasks: ParallelTask[] = [];
  const pickCount = Math.min(PARALLEL_COUNT, categories.length, agents.length);

  for (let i = 0; i < pickCount; i += 1) {
    const category = categories[(round + i) % categories.length];
    const pool = grouped[category];
    if (!pool?.length) continue;

    const agent = pool[(round + i) % pool.length];
    if (activeAgentIds.includes(agent.id)) continue;

    activeAgentIds.push(agent.id);
    tasks.push({
      agentId: agent.id,
      agentName: agent.name,
      category,
      task: getSimulatedTask(agent.id, category),
    });
  }

  return {
    activeAgentIds,
    activeInputId,
    activeModelId,
    modelActive: tasks.length > 0,
    modelTask: tasks.length > 0 ? getSimulatedModelTask(engine) : "",
    pipelineLabel:
      tasks.length > 0
        ? `${inputLabel(activeInputId)} → ${modelName} (${engine}) → Orchestrator → ${tasks.length} agents parallel`
        : "",
    tasks,
  };
}
