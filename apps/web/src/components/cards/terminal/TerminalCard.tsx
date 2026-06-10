import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { TerminalWidget } from "./TerminalWidget";

export default function TerminalCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <TerminalWidget payload={card.payload} />
    </CardShell>
  );
}
