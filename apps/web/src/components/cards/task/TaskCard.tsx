import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function TaskCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <div className="text-sm space-y-1">
        <p className="text-on-surface-variant">{String(card.payload.kind ?? "task")}</p>
        {card.payload.parallel_group ? (
          <p className="text-xs text-on-surface-variant/70">
            Group: {String(card.payload.parallel_group)}
          </p>
        ) : null}
      </div>
    </CardShell>
  );
}
