/**
 * Reducer for hierarchical agent task events (SSE `task` + legacy tool/agent events).
 */

import { agentsForTool } from "./agentSimulation";

export type TaskStatus = "pending" | "active" | "success" | "error";

export interface AgentTaskNode {
  id: string;
  parentId?: string;
  title: string;
  kind: "agent" | "tool" | "plan" | "memory" | "status" | "model";
  status: TaskStatus;
  depth: number;
  parallelGroup?: string;
  agentId?: string;
}

export interface TaskStreamEvent {
  type: string;
  task_id?: string;
  parent_id?: string;
  kind?: string;
  name?: string;
  title?: string;
  status?: string;
  agent_id?: string;
  parallel_group?: string;
  depth?: number;
  content?: string;
}

export function agentForTool(toolName: string, agentId?: string): string[] {
  const ids = new Set<string>(["main", ...agentsForTool(toolName, agentId)]);
  return Array.from(ids);
}

function normalizeStatus(status?: string): TaskStatus {
  if (status === "success" || status === "done" || status === "completed") return "success";
  if (status === "error" || status === "failed") return "error";
  if (status === "pending") return "pending";
  return "active";
}

function upsertTask(tasks: AgentTaskNode[], node: AgentTaskNode): AgentTaskNode[] {
  const idx = tasks.findIndex((t) => t.id === node.id);
  if (idx < 0) return [...tasks, node];
  const next = [...tasks];
  next[idx] = { ...next[idx], ...node };
  return next;
}

function humanize(name: string): string {
  return name.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function reduceAgentTasks(
  tasks: AgentTaskNode[],
  event: TaskStreamEvent
): AgentTaskNode[] {
  if (event.type === "task" && event.task_id) {
    return upsertTask(tasks, {
      id: event.task_id,
      parentId: event.parent_id,
      title: event.title || humanize(event.name || "Task"),
      kind: (event.kind as AgentTaskNode["kind"]) || "tool",
      status: normalizeStatus(event.status),
      depth: event.depth ?? 0,
      parallelGroup: event.parallel_group,
      agentId: event.agent_id || (event.kind === "agent" ? event.name : undefined),
    });
  }

  if (event.type === "agent" || event.type === "subagent") {
    const agentId = event.agent_id || event.name || "main";
    const id = `agent:${agentId}:${event.type}`;
    const parentId = event.type === "subagent" ? "root" : undefined;
    return upsertTask(tasks, {
      id,
      parentId,
      title: `${event.type === "subagent" ? "Delegate" : "Run"} ${humanize(agentId)}`,
      kind: "agent",
      status: normalizeStatus(event.status),
      depth: event.type === "subagent" ? 1 : 0,
      agentId,
    });
  }

  if (event.type === "tool" && event.name) {
    const id = `tool:${event.name}${event.agent_id ? `:${event.agent_id}` : ""}`;
    const title =
      event.name === "invoke_agent" && event.agent_id
        ? `Delegate ${humanize(event.agent_id)}`
        : event.name === "parallel_invoke_agents"
          ? "Parallel agents"
          : `Tool: ${humanize(event.name)}`;
    return upsertTask(tasks, {
      id,
      parentId: "root",
      title,
      kind: "tool",
      status: normalizeStatus(event.status),
      depth: 1,
      agentId: event.agent_id,
    });
  }

  if (event.type === "memory" && event.name) {
    return upsertTask(tasks, {
      id: `memory:${event.name}`,
      parentId: "root",
      title: `Memory: ${humanize(event.name)}`,
      kind: "memory",
      status: normalizeStatus(event.status),
      depth: 1,
    });
  }

  if (event.type === "model" && event.content) {
    return upsertTask(tasks, {
      id: "model",
      title: `Model: ${event.content}`,
      kind: "model",
      status: "success",
      depth: 0,
    });
  }

  if (event.type === "status" && event.content) {
    return upsertTask(tasks, {
      id: `status:${tasks.length}`,
      parentId: "root",
      title: event.content,
      kind: "status",
      status: "success",
      depth: 1,
    });
  }

  return tasks;
}

/** Flat list for TaskPanel with tree indentation via depth. */
export function tasksToPanelItems(tasks: AgentTaskNode[]): {
  id: string;
  text: string;
  active?: boolean;
  depth?: number;
  parallelGroup?: string;
}[] {
  const sorted = [...tasks].sort((a, b) => {
    if (a.depth !== b.depth) return a.depth - b.depth;
    return a.id.localeCompare(b.id);
  });
  return sorted.map((t) => ({
    id: t.id,
    text: `${"  ".repeat(Math.max(0, t.depth))}${t.parallelGroup ? "⇉ " : ""}${t.title}`,
    active: t.status === "active",
    depth: t.depth,
    parallelGroup: t.parallelGroup,
  }));
}

export function activeAgentsFromTasks(tasks: AgentTaskNode[]): string[] {
  const active = new Set<string>();
  for (const t of tasks) {
    if (t.status !== "active") continue;
    if (t.agentId) active.add(t.agentId);
    if (t.kind === "agent" && t.agentId) active.add(t.agentId);
    if (t.kind === "tool" && t.agentId) active.add(t.agentId);
    if (t.kind === "tool") {
      const toolName = t.id.replace(/^tool:/, "").split(":")[0];
      for (const aid of agentsForTool(toolName, t.agentId)) active.add(aid);
    }
  }
  if (tasks.some((t) => t.status === "active")) active.add("main");
  return Array.from(active);
}

export function activeToolsFromTasks(tasks: AgentTaskNode[]): string[] {
  return tasks
    .filter((t) => t.kind === "tool" && t.status === "active")
    .map((t) => t.id.replace(/^tool:/, "").split(":")[0]);
}

export function memoryActiveFromTasks(tasks: AgentTaskNode[]): boolean {
  return tasks.some((t) => t.kind === "memory" && t.status === "active");
}
