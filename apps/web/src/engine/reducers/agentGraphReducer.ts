import type { AgentGraphState, AiEventEnvelope } from "../types";

export function agentGraphReducer(
  state: AgentGraphState,
  events: AiEventEnvelope[]
): AgentGraphState {
  let next = { ...state };

  for (const event of events) {
    const p = event.payload;
    const legacy = event.legacy_type;

    if (event.type === "model.resolved" || legacy === "model") {
      next = { ...next, modelActive: true, activeModelId: String(p.model_id ?? next.activeModelId ?? "") };
    }

    if (event.type === "agent.started" || legacy === "agent") {
      const agentId = String(p.agent_id ?? "");
      if (agentId) {
        const ids = new Set(next.activeAgentIds);
        if (p.status === "success") {
          ids.delete(agentId);
        } else {
          ids.add(agentId);
        }
        next = { ...next, activeAgentIds: [...ids] };
      }
    }

    if (event.type === "agent.delegated" || legacy === "subagent") {
      const agentId = String(p.agent_id ?? "");
      if (agentId) {
        const ids = new Set(next.activeAgentIds);
        ids.add(agentId);
        next = { ...next, activeAgentIds: [...ids] };
      }
    }

    if (event.type === "tool.started" || event.type === "tool.finished" || legacy === "tool") {
      const toolName = String(p.tool_name ?? p.name ?? "");
      if (toolName) {
        const tools = new Set(next.activeTools);
        if (p.status === "success" || event.type === "tool.finished") {
          tools.delete(toolName);
        } else {
          tools.add(toolName);
        }
        next = { ...next, activeTools: [...tools] };
      }
    }

    if (event.type === "memory.active" || legacy === "memory") {
      next = { ...next, memoryActive: p.status !== "success" };
    }

    if (event.type === "workflow.node" || legacy === "task") {
      if (p.kind === "model") {
        next = { ...next, modelActive: p.status === "active", activeModelId: String(p.title ?? "").replace(/^Model:\s*/i, "") || next.activeModelId };
      }
      if (p.kind === "agent" && p.agent_id) {
        const ids = new Set(next.activeAgentIds);
        if (p.status === "success") ids.delete(String(p.agent_id));
        else ids.add(String(p.agent_id));
        next = { ...next, activeAgentIds: [...ids] };
      }
      if (p.kind === "tool" && p.name) {
        const tools = new Set(next.activeTools);
        if (p.status === "success") tools.delete(String(p.name));
        else tools.add(String(p.name));
        next = { ...next, activeTools: [...tools] };
      }
    }

    if (event.type === "stream.done") {
      next = { ...next, modelActive: false };
    }
  }

  return next;
}
