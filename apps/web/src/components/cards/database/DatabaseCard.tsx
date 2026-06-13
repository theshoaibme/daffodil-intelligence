import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { TableViewerWidget } from "./TableViewerWidget";

export default function DatabaseCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <TableViewerWidget payload={card.payload} />
    </CardShell>
  );
}
