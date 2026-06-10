import type { Card } from "./types";

export const EXCLUDED_THREAD_CARD_TYPES = new Set(["block", "result"]);
export const DOCK_CARD_TYPES = new Set(["agent", "workflow", "task"]);

export interface ThreadCardFilterOptions {
  excludeTypes?: Iterable<string>;
  inlineOnly?: boolean;
  turnId?: string | null;
}

export function filterThreadCards(
  card: Card,
  { excludeTypes = EXCLUDED_THREAD_CARD_TYPES, inlineOnly = true, turnId }: ThreadCardFilterOptions = {}
): boolean {
  const excluded = excludeTypes instanceof Set ? excludeTypes : new Set(excludeTypes);

  if (excluded.has(card.card_type)) return false;
  if (inlineOnly && DOCK_CARD_TYPES.has(card.card_type)) return false;
  if (turnId && card.turn_id && card.turn_id !== turnId) return false;
  return true;
}
