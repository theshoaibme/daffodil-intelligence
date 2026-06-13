import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function ApprovalCard({ card }: { card: Card }) {
  const action = String(card.payload.action ?? "action");
  const description = String(card.payload.description ?? "");

  return (
    <CardShell card={card}>
      <div className="space-y-3">
        <p className="text-sm">{description || `Approve ${action}?`}</p>
        <div className="flex gap-2">
          <button type="button" className="px-3 py-1.5 text-xs rounded-lg bg-primary text-on-primary">
            Approve
          </button>
          <button type="button" className="px-3 py-1.5 text-xs rounded-lg border border-outline-variant/40">
            Deny
          </button>
        </div>
      </div>
    </CardShell>
  );
}
