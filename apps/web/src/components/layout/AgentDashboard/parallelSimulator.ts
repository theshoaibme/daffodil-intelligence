import type { Agent } from "../../../hooks/useAgents";
import { INPUT_INTEGRATIONS } from "./graphBuilder";
import { getSimulatedTask } from "./simulatorTasks";

export interface ParallelTask {
  agentId: string;
  agentName: string;
  category: string;
  task: string;
}

export interface ParallelSimulationState {
  activeAgentIds: string[];
  activeInputId: string;
  tasks: ParallelTask[];
}

const PARALLEL_COUNT = 3;

export function nextParallelSimulation(agents: Agent[], round: number): ParallelSimulationState {
  const busy = agents.filter((a) => a.status === "executing" || a.status === "thinking");
  if (busy.length > 0) {
    const activeAgentIds = busy.slice(0, PARALLEL_COUNT).map((a) => a.id);
    return {
      activeAgentIds,
      activeInputId: INPUT_INTEGRATIONS[round % INPUT_INTEGRATIONS.length].id,
      tasks: busy.slice(0, PARALLEL_COUNT).map((agent) => ({
        agentId: agent.id,
        agentName: agent.name,
        category: agent.category,
        task: agent.currentTask || getSimulatedTask(agent.id, agent.category),
      })),
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
    return { activeAgentIds: [], activeInputId: INPUT_INTEGRATIONS[0].id, tasks: [] };
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
    activeInputId: INPUT_INTEGRATIONS[round % INPUT_INTEGRATIONS.length].id,
    tasks,
  };
}
