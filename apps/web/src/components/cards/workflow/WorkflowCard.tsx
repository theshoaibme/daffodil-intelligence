import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function WorkflowCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <p className="text-sm text-on-surface-variant">
        {card.payload.node_count != null
          ? `${card.payload.node_count} nodes`
          : "Workflow"}
      </p>
    </CardShell>
  );
}
