import { eventToCardSpec } from "../reducers/cardsReducer";
import type { AiEventEnvelope, Card, CardType } from "../types";

const BLOCK_SCHEMA_TO_CARD: Record<string, CardType> = {
  data_table: "database",
  key_value: "result",
  tabs: "block",
  status_card: "result",
  error_alert: "result",
};

export function eventToCard(event: AiEventEnvelope): Card | null {
  const base = eventToCardSpec(event);
  if (!base) return null;

  if (event.type === "ui.block" && event.payload.block) {
    const block = event.payload.block as Record<string, unknown>;
    const schema = String(block.schema ?? "");
    return {
      ...base,
      card_type: BLOCK_SCHEMA_TO_CARD[schema] ?? "block",
      payload: { ...base.payload, block },
    };
  }

  return base;
}

export function sortCards(cards: Card[]): Card[] {
  return [...cards].sort(
    (a, b) => a.priority - b.priority || a.timestamp.localeCompare(b.timestamp)
  );
}
