import { Suspense, useMemo, useRef, useState, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { resolveCardComponent } from "../../engine/registries/ComponentRegistry";
import { sortCards } from "../../engine/registries/CardRegistry";
import { useEventStore } from "../../engine/stores/eventStore";
import type { Card } from "../../engine/types";
import { CardSkeleton } from "../cards/CardShell";

const ESTIMATED_CARD_HEIGHT = 120;
const OVERSCAN = 3;

interface VirtualCardCanvasProps {
  sessionId: string;
  filter?: (card: Card) => boolean;
  className?: string;
}

export function VirtualCardCanvas({ sessionId, filter, className }: VirtualCardCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(600);

  const cards = useEventStore(
    useShallow((s) => {
      const sorted = sortCards(s.sessions[sessionId]?.cards ?? []);
      return filter ? sorted.filter(filter) : sorted;
    })
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setViewportHeight(el.clientHeight));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { start, end, totalHeight } = useMemo(() => {
    const total = cards.length * ESTIMATED_CARD_HEIGHT;
    const startIdx = Math.max(0, Math.floor(scrollTop / ESTIMATED_CARD_HEIGHT) - OVERSCAN);
    const visibleCount = Math.ceil(viewportHeight / ESTIMATED_CARD_HEIGHT) + OVERSCAN * 2;
    const endIdx = Math.min(cards.length, startIdx + visibleCount);
    return {
      start: startIdx,
      end: endIdx,
      totalHeight: total,
    };
  }, [cards.length, scrollTop, viewportHeight]);

  const visible = cards.slice(start, end);

  if (!cards.length) return null;

  return (
    <div
      ref={containerRef}
      className={className ?? "flex flex-col w-full overflow-y-auto max-h-[60vh]"}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div style={{ height: totalHeight, position: "relative" }}>
        <div
          style={{
            position: "absolute",
            top: start * ESTIMATED_CARD_HEIGHT,
            left: 0,
            right: 0,
          }}
          className="flex flex-col gap-3"
        >
          {visible.map((card) => {
            const Component = resolveCardComponent(card.card_type);
            return (
              <Suspense key={card.id} fallback={<CardSkeleton type={card.card_type} />}>
                <Component card={card} />
              </Suspense>
            );
          })}
        </div>
      </div>
    </div>
  );
}
