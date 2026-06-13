import type { AiEventEnvelope, Card, CardStatus, CardType } from "../types";

function statusFromEvent(type: string, payload: Record<string, unknown>): CardStatus {
  const raw = String(payload.status ?? "");
  if (raw === "success" || type.endsWith(".finished")) return "success";
  if (raw === "error" || type.endsWith(".error")) return "error";
  if (raw === "cancelled") return "cancelled";
  if (raw === "active" || type.endsWith(".started") || type.endsWith(".progress")) return "active";
  return "pending";
}

function cardIdFromEvent(event: AiEventEnvelope): string {
  const p = event.payload;
  if (event.type === "workflow.node" && p.task_id) return `task-${p.task_id}`;
  if (event.type.startsWith("tool.") && p.tool_name) return `tool-${p.tool_name}-${event.turn_id}`;
  if (event.type.startsWith("agent.") && p.agent_id) return `agent-${p.agent_id}`;
  if (event.type === "ui.block" && p.block) {
    const block = p.block as Record<string, unknown>;
    return String(block.id ?? `block-${event.id}`);
  }
  if (event.type === "approval.required" && p.approval_id) return `approval-${p.approval_id}`;
  if (event.type === "file.created" && p.file_id) return `file-${p.file_id}`;
  if (event.type === "image.created" && p.image_id) return `image-${p.image_id}`;
  return `card-${event.id}`;
}

function cardTypeFromEvent(event: AiEventEnvelope): CardType {
  const map: Record<string, CardType> = {
    "agent.started": "agent",
    "agent.finished": "agent",
    "agent.delegated": "agent",
    "agent.action": "agent",
    "agent.thought": "agent",
    "tool.started": "tool",
    "tool.finished": "tool",
    "tool.progress": "tool",
    "tool.result": "result",
    "workflow.node": "task",
    "workflow.started": "workflow",
    "ui.block": "block",
    "approval.required": "approval",
    "form.request": "form",
    "file.created": "file",
    "image.created": "image",
  };
  return map[event.type] ?? "result";
}

function titleFromEvent(event: AiEventEnvelope): string {
  const p = event.payload;
  if (p.title) return String(p.title);
  if (p.name) return String(p.name);
  if (p.tool_name) return String(p.tool_name);
  if (p.agent_id) return String(p.agent_id);
  if (event.type === "ui.block" && p.block) {
    const block = p.block as Record<string, unknown>;
    return String(block.title ?? block.schema ?? "Block");
  }
  return event.type.replace(/\./g, " ");
}

function mergeCard(existing: Card, event: AiEventEnvelope): Card {
  const p = event.payload;
  return {
    ...existing,
    status: statusFromEvent(event.type, p),
    title: titleFromEvent(event) || existing.title,
    subtitle: p.short_title ? String(p.short_title) : existing.subtitle,
    timestamp: event.ts,
    payload: { ...existing.payload, ...p },
    turn_id: event.turn_id,
    correlation_id: event.correlation_id,
  };
}

export function eventToCardSpec(event: AiEventEnvelope): Card | null {
  const skip = new Set(["message.chunk", "message.thinking", "message.completed", "context.usage", "model.resolved", "status.progress", "memory.active", "stream.done"]);
  if (skip.has(event.type)) return null;

  const p = event.payload;
  return {
    id: cardIdFromEvent(event),
    card_type: cardTypeFromEvent(event),
    status: statusFromEvent(event.type, p),
    title: titleFromEvent(event),
    subtitle: p.short_title ? String(p.short_title) : undefined,
    icon: p.icon ? String(p.icon) : undefined,
    timestamp: event.ts,
    source: event.source ?? {},
    layout: "inline",
    priority: event.type.startsWith("agent.") ? 10 : event.type.startsWith("tool.") ? 20 : 30,
    collapsible: true,
    payload: { ...p },
    turn_id: event.turn_id,
    correlation_id: event.correlation_id,
  };
}

export function cardsReducer(cards: Card[], events: AiEventEnvelope[]): Card[] {
  let next = [...cards];
  for (const event of events) {
    const spec = eventToCardSpec(event);
    if (!spec) continue;
    const idx = next.findIndex((c) => c.id === spec.id);
    if (idx === -1) {
      next = [...next, spec];
    } else {
      next = next.map((c, i) => (i === idx ? mergeCard(c, event) : c));
    }
  }
  return next.sort((a, b) => a.priority - b.priority || a.timestamp.localeCompare(b.timestamp));
}

export function clearCardsForTurn(cards: Card[], turnId: string): Card[] {
  return cards.filter((c) => c.turn_id !== turnId);
}
