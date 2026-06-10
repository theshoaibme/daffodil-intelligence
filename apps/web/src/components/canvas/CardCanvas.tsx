import { Suspense, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { resolveCardComponent } from "../../engine/registries/ComponentRegistry";
import { sortCards } from "../../engine/registries/CardRegistry";
import { useEventStore } from "../../engine/stores/eventStore";
import type { Card } from "../../engine/types";
import { CardSkeleton } from "../cards/CardShell";

interface CardCanvasProps {
  sessionId: string;
  filter?: (card: Card) => boolean;
  className?: string;
}

export function CardCanvas({ sessionId, filter, className }: CardCanvasProps) {
  const cards = useEventStore(
    useShallow((s) => sortCards(s.sessions[sessionId]?.cards ?? []))
  );

  const visible = useMemo(
    () => (filter ? cards.filter(filter) : cards),
    [cards, filter]
  );

  if (!visible.length) return null;

  return (
    <div className={className ?? "flex flex-col gap-3 w-full"}>
      {visible.map((card) => {
        const Component = resolveCardComponent(card.card_type);
        return (
          <Suspense key={card.id} fallback={<CardSkeleton type={card.card_type} />}>
            <Component card={card} />
          </Suspense>
        );
      })}
    </div>
  );
}
