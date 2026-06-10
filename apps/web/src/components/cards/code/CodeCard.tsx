import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { CodeViewerWidget } from "./CodeViewerWidget";

export default function CodeCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <CodeViewerWidget payload={card.payload} />
    </CardShell>
  );
}
