import { lazy, type ComponentType, type LazyExoticComponent } from "react";
import type { Card } from "../types";

export type CardComponent = ComponentType<{ card: Card }>;

const registry = new Map<string, LazyExoticComponent<CardComponent>>();

const lazyCards: Record<string, () => Promise<{ default: CardComponent }>> = {
  agent: () => import("../../components/cards/agent/AgentCard"),
  tool: () => import("../../components/cards/tool/ToolCard"),
  task: () => import("../../components/cards/task/TaskCard"),
  workflow: () => import("../../components/cards/workflow/WorkflowCard"),
  search: () => import("../../components/cards/search/SearchCard"),
  file: () => import("../../components/cards/file/FileCard"),
  code: () => import("../../components/cards/code/CodeCard"),
  image: () => import("../../components/cards/image/ImageCard"),
  browser: () => import("../../components/cards/browser/BrowserCard"),
  result: () => import("../../components/cards/result/ResultCard"),
  approval: () => import("../../components/cards/approval/ApprovalCard"),
  form: () => import("../../components/cards/form/FormCard"),
  terminal: () => import("../../components/cards/terminal/TerminalCard"),
  database: () => import("../../components/cards/database/DatabaseCard"),
  block: () => import("../../components/cards/block/BlockCard"),
};

export function registerCardType(
  cardType: string,
  loader: () => Promise<{ default: CardComponent }>
) {
  registry.set(cardType, lazy(loader));
}

export function resolveCardComponent(cardType: string): LazyExoticComponent<CardComponent> {
  if (!registry.has(cardType)) {
    const loader = lazyCards[cardType] ?? lazyCards.result;
    registry.set(cardType, lazy(loader));
  }
  return registry.get(cardType)!;
}

// Pre-register built-in types
for (const [type, loader] of Object.entries(lazyCards)) {
  registerCardType(type, loader);
}
