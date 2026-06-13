import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { GenericResultWidget } from "./GenericResultWidget";

export default function ResultCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <GenericResultWidget payload={card.payload} />
    </CardShell>
  );
}
