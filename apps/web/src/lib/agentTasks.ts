/**
 * Reducer for hierarchical agent task events (SSE `task` + legacy tool/agent events).
 */

import { agentsForTool } from "./agentSimulation";

export type TaskStatus = "pending" | "active" | "success" | "error";

export interface AgentTaskNode {
  id: string;
  parentId?: string;
  title: string;
  shortTitle?: string;
  name?: string;
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
  short_title?: string;
  status?: string;
  agent_id?: string;
  parallel_group?: string;
  depth?: number;
  content?: string;
  source?: string;
  mcp_server?: string;
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

function isStructuredTaskGraph(tasks: AgentTaskNode[]): boolean {
  return tasks.some((t) => t.id.startsWith("task-") || t.id.startsWith("root-"));
}

function orderTasksTree(tasks: AgentTaskNode[]): AgentTaskNode[] {
  if (tasks.length <= 1) return tasks;

  const byId = new Map(tasks.map((t) => [t.id, t]));
  const childrenOf = new Map<string, AgentTaskNode[]>();
  const roots: AgentTaskNode[] = [];

  for (const task of tasks) {
    const parentId = task.parentId;
    if (parentId && byId.has(parentId)) {
      const siblings = childrenOf.get(parentId) ?? [];
      siblings.push(task);
      childrenOf.set(parentId, siblings);
    } else {
      roots.push(task);
    }
  }

  const ordered: AgentTaskNode[] = [];
  const seen = new Set<string>();

  const visit = (node: AgentTaskNode) => {
    if (seen.has(node.id)) return;
    seen.add(node.id);
    ordered.push(node);
    for (const child of childrenOf.get(node.id) ?? []) {
      visit(child);
    }
  };

  const rootOrder = [...roots].sort((a, b) => a.depth - b.depth || tasks.indexOf(a) - tasks.indexOf(b));
  for (const root of rootOrder) {
    visit(root);
  }

  for (const task of tasks) {
    if (!seen.has(task.id)) {
      ordered.push(task);
    }
  }

  return ordered;
}

export function reduceAgentTasks(
  tasks: AgentTaskNode[],
  event: TaskStreamEvent
): AgentTaskNode[] {
  if (event.type === "task" && event.task_id) {
    const next = upsertTask(tasks, {
      id: event.task_id,
      parentId: event.parent_id,
      title: event.title || humanize(event.name || "Task"),
      shortTitle: event.short_title,
      name: event.name,
      kind: (event.kind as AgentTaskNode["kind"]) || "tool",
      status: normalizeStatus(event.status),
      depth: event.depth ?? 0,
      parallelGroup: event.parallel_group,
      agentId: event.agent_id || (event.kind === "agent" ? event.name : undefined),
    });
    return next.filter((t) => !t.id.startsWith("agent:") && !t.id.startsWith("tool:"));
  }

  if (event.type === "agent" || event.type === "subagent") {
    if (isStructuredTaskGraph(tasks)) {
      return tasks;
    }
    const agentId = event.agent_id || event.name || "main";
    if (tasks.some((t) => t.kind === "agent" && t.agentId === agentId && t.id.startsWith("task-"))) {
      return tasks;
    }
    const id = `agent:${agentId}:${event.type}`;
    const parentId = event.type === "subagent" ? "root" : undefined;
    return upsertTask(tasks, {
      id,
      parentId,
      title:
        event.type === "subagent" && agentId === "routine"
          ? "Routine Agent"
          : `${event.type === "subagent" ? "Delegate" : "Run"} ${humanize(agentId)}`,
      kind: "agent",
      status: normalizeStatus(event.status),
      depth: event.type === "subagent" ? 1 : 0,
      agentId,
    });
  }

  if (event.type === "tool" && event.name) {
    if (isStructuredTaskGraph(tasks)) {
      const match = tasks.find((t) => t.kind === "tool" && t.name === event.name);
      if (match) {
        return upsertTask(tasks, {
          ...match,
          status: normalizeStatus(event.status),
        });
      }
      return tasks;
    }
    if (tasks.some((t) => t.kind === "tool" && t.name === event.name)) {
      return tasks;
    }
    const id = `tool:${event.name}${event.agent_id ? `:${event.agent_id}` : ""}`;
    let title =
      event.name === "invoke_agent" && event.agent_id
        ? `Delegate ${humanize(event.agent_id)}`
        : event.name === "parallel_invoke_agents"
          ? "Parallel agents"
          : event.name === "get_class_routine"
            ? "Load class routine"
            : `Tool: ${humanize(event.name)}`;
    if (event.source === "mcp") {
      title = `MCP · ${humanize(event.mcp_server ?? "server")} · ${humanize(event.name)}`;
    }
    const parentId = event.agent_id ? `agent:${event.agent_id}:subagent` : "root";
    const depth = event.agent_id ? 2 : 1;
    return upsertTask(tasks, {
      id,
      parentId,
      title,
      name: event.name,
      kind: "tool",
      status: normalizeStatus(event.status),
      depth,
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
      status: "active",
      depth: 0,
    });
  }

  if (event.type === "status" && event.content) {
    const slug = event.content.slice(0, 48).replace(/\s+/g, "-").toLowerCase();
    return upsertTask(tasks, {
      id: `status:${slug}`,
      parentId: "root",
      title: event.content,
      kind: "status",
      status: "success",
      depth: 1,
    });
  }

  return tasks;
}

export interface TaskPanelItem {
  id: string;
  text: string;
  active?: boolean;
  depth?: number;
  parallelGroup?: string;
  kind?: AgentTaskNode["kind"];
  status?: TaskStatus;
}

const PANEL_HIDDEN_KINDS = new Set<AgentTaskNode["kind"]>(["model", "memory", "status"]);

/** True when a task row should appear in the Task manager UI (not trace/metadata). */
export function hasActivePanelWork(tasks: AgentTaskNode[]): boolean {
  return tasks.some((task) => task.status === "active" && isPanelVisibleTask(task));
}

export function isPanelVisibleTask(task: AgentTaskNode): boolean {
  if (PANEL_HIDDEN_KINDS.has(task.kind)) return false;

  if (task.kind === "agent") {
    const title = task.title.toLowerCase();
    if (title.startsWith("orchestrator")) return false;
    const agentId = (task.agentId || task.name || "").toLowerCase();
    if (task.depth === 0 && (agentId === "main" || agentId === "supervisor" || agentId === "default")) {
      return false;
    }
    if (task.id.startsWith("agent:") && task.id.endsWith(":agent") && task.depth === 0) {
      return false;
    }
  }

  return true;
}

const SHORT_TITLE_MAX_LEN = 48;

/** Prefer backend `short_title`; otherwise strip prefixes and truncate. */
export function shortTitle(title: string, backendShortTitle?: string): string {
  const trimmed = backendShortTitle?.trim();
  if (trimmed) return trimmed;

  let text = title
    .replace(/^Tool:\s*/i, "")
    .replace(/^Agent:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
  if (text.length <= SHORT_TITLE_MAX_LEN) return text;
  return `${text.slice(0, SHORT_TITLE_MAX_LEN - 1).trimEnd()}…`;
}

function panelTaskText(task: AgentTaskNode): string {
  const text = shortTitle(task.title, task.shortTitle);
  if (task.parallelGroup) {
    return `⇉ ${text}`;
  }
  return text;
}

/** Flat list for TaskPanel — parent → child order, indentation via depth only. */
export function tasksToPanelItems(tasks: AgentTaskNode[]): TaskPanelItem[] {
  const visible = orderTasksTree(tasks).filter(isPanelVisibleTask);
  const minDepth = visible.reduce((min, t) => Math.min(min, t.depth), Number.POSITIVE_INFINITY);
  let topLevelIndex = 0;

  return visible.map((t) => {
    const isTopLevel = t.depth === minDepth;
    let text: string;
    if (isTopLevel) {
      topLevelIndex += 1;
      const short = shortTitle(t.title, t.shortTitle);
      const body = t.parallelGroup ? `⇉ ${short}` : short;
      text = `Task ${topLevelIndex}: ${body}`;
    } else {
      text = panelTaskText(t);
    }

    return {
      id: t.id,
      text,
      active: t.status === "active",
      depth: Number.isFinite(minDepth) ? Math.max(0, t.depth - minDepth) : t.depth,
      parallelGroup: t.parallelGroup,
      kind: t.kind,
      status: t.status,
    };
  });
}

export function activeAgentsFromTasks(tasks: AgentTaskNode[]): string[] {
  const active = new Set<string>();
  for (const t of tasks) {
    if (t.status !== "active") continue;
    if (t.agentId) active.add(t.agentId);
    if (t.kind === "agent" && t.agentId) active.add(t.agentId);
    if (t.kind === "tool" && t.agentId) active.add(t.agentId);
    if (t.kind === "tool") {
      const toolName = t.name || t.id.replace(/^tool:/, "").split(":")[0];
      if (toolName) {
        for (const aid of agentsForTool(toolName, t.agentId)) active.add(aid);
      }
    }
  }
  if (tasks.some((t) => t.status === "active")) active.add("main");
  return Array.from(active);
}

export function activeToolsFromTasks(tasks: AgentTaskNode[]): string[] {
  return tasks
    .filter((t) => t.kind === "tool" && t.status === "active")
    .map((t) => t.name || t.id.replace(/^tool:/, "").split(":")[0])
    .filter(Boolean);
}

export function memoryActiveFromTasks(tasks: AgentTaskNode[]): boolean {
  return tasks.some((t) => t.kind === "memory" && t.status === "active");
}
