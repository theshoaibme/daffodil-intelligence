import type { AiEventEnvelope } from "../engine/types";
import type { StreamEvent } from "./api";

const LEGACY_TO_CANONICAL: Record<string, string> = {
  content: "message.chunk",
  thinking: "message.thinking",
  status: "status.progress",
  tool: "tool.started",
  agent: "agent.started",
  subagent: "agent.delegated",
  memory: "memory.active",
  task: "workflow.node",
  ui: "ui.block",
  model: "model.resolved",
  context: "context.usage",
};

export function parseEnvelope(
  parsed: Record<string, unknown>,
  sessionId: string,
  turnId?: string
): AiEventEnvelope | null {
  if (parsed.envelope && typeof parsed.envelope === "object") {
    const env = parsed.envelope as AiEventEnvelope;
    return {
      ...env,
      session_id: env.session_id || sessionId,
      turn_id: env.turn_id || turnId || env.turn_id,
    };
  }

  const legacyType = String(parsed.type ?? "content");
  const canonical = LEGACY_TO_CANONICAL[legacyType] ?? legacyType;

  const payload: Record<string, unknown> = {};
  if (legacyType === "content") payload.content = parsed.content;
  else if (legacyType === "thinking") payload.content = parsed.content;
  else if (legacyType === "status") payload.content = parsed.content;
  else if (legacyType === "tool") {
    payload.tool_name = parsed.name;
    payload.name = parsed.name;
    payload.status = parsed.status;
    payload.agent_id = parsed.agent_id;
    payload.source = parsed.source;
    payload.mcp_server = parsed.mcp_server;
    if (parsed.status === "success") {
      return {
        v: 1,
        id: `legacy-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        seq: 0,
        ts: new Date().toISOString(),
        session_id: sessionId,
        turn_id: turnId ?? "",
        source: {
          agent_id: parsed.agent_id as string | undefined,
          tool_name: parsed.name as string | undefined,
          mcp_server: parsed.mcp_server as string | undefined,
        },
        type: "tool.finished",
        payload,
        legacy_type: legacyType,
      };
    }
  } else if (legacyType === "agent") {
    payload.agent_id = parsed.agent_id;
    payload.name = parsed.name;
    payload.status = parsed.status;
  } else if (legacyType === "subagent") {
    payload.agent_id = parsed.agent_id;
    payload.name = parsed.name;
    payload.status = parsed.status;
    payload.content = parsed.content;
  } else if (legacyType === "memory") {
    payload.name = parsed.name;
    payload.status = parsed.status;
  } else if (legacyType === "task") {
    Object.assign(payload, parsed);
    delete payload.type;
  } else if (legacyType === "ui") {
    payload.block = parsed.block;
    payload.source = parsed.source;
    payload.tool_name = parsed.tool_name;
  } else if (legacyType === "model") {
    payload.model_id = parsed.model_id;
    payload.model_mode = parsed.model_mode;
    payload.model_routing = parsed.model_routing;
  } else if (legacyType === "context") {
    Object.assign(payload, parsed);
    delete payload.type;
  }

  return {
    v: 1,
    id: `legacy-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    seq: Number(parsed.seq ?? 0),
    ts: new Date().toISOString(),
    session_id: sessionId,
    turn_id: turnId ?? String(parsed.turn_id ?? ""),
    source: {
      agent_id: parsed.agent_id as string | undefined,
      tool_name: (parsed.tool_name ?? parsed.name) as string | undefined,
      mcp_server: parsed.mcp_server as string | undefined,
    },
    type: canonical,
    payload,
    legacy_type: legacyType,
  };
}

export function envelopeToStreamEvent(envelope: AiEventEnvelope): StreamEvent | null {
  const legacy = envelope.legacy_type;
  const p = envelope.payload;

  if (legacy === "thinking" || envelope.type === "message.thinking") {
    return { type: "thinking", content: String(p.content ?? "") };
  }
  if (legacy === "status" || envelope.type === "status.progress") {
    return { type: "status", content: String(p.content ?? "") };
  }
  if (legacy === "model" || envelope.type === "model.resolved") {
    return { type: "model", content: String(p.model_id ?? ""), name: String(p.model_routing ?? "") };
  }
  if (legacy === "ui" || envelope.type === "ui.block") {
    return {
      type: "ui",
      block: p.block as StreamEvent["block"],
      source: p.source as string | undefined,
      tool_name: p.tool_name as string | undefined,
    };
  }
  if (legacy === "tool" || envelope.type.startsWith("tool.")) {
    return {
      type: "tool",
      name: String(p.tool_name ?? p.name ?? ""),
      status: String(p.status ?? "active"),
      agent_id: p.agent_id as string | undefined,
      source: p.source as string | undefined,
      mcp_server: p.mcp_server as string | undefined,
    };
  }
  if (legacy === "memory" || envelope.type === "memory.active") {
    return { type: "memory", name: String(p.name ?? "memory"), status: String(p.status ?? "active") };
  }
  if (legacy === "task" || envelope.type === "workflow.node") {
    return {
      type: "task",
      task_id: p.task_id as string | undefined,
      parent_id: p.parent_id as string | undefined,
      kind: p.kind as string | undefined,
      name: p.name as string | undefined,
      title: p.title as string | undefined,
      short_title: p.short_title as string | undefined,
      status: p.status as string | undefined,
      agent_id: p.agent_id as string | undefined,
      parallel_group: p.parallel_group as string | undefined,
      depth: p.depth as number | undefined,
    };
  }
  if (legacy === "agent" || envelope.type === "agent.started") {
    return {
      type: "agent",
      name: p.name as string | undefined,
      status: p.status as string | undefined,
      agent_id: p.agent_id as string | undefined,
    };
  }
  if (legacy === "subagent" || envelope.type === "agent.delegated") {
    return {
      type: "subagent",
      name: p.name as string | undefined,
      status: p.status as string | undefined,
      agent_id: p.agent_id as string | undefined,
      content: p.content as string | undefined,
    };
  }
  return null;
}
