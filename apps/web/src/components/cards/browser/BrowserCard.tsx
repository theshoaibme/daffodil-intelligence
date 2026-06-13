import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { BrowserSessionWidget } from "./BrowserSessionWidget";

export default function BrowserCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <BrowserSessionWidget payload={card.payload} />
    </CardShell>
  );
}
