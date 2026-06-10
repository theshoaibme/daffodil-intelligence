import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { FilePreviewWidget } from "./FilePreviewWidget";

export default function FileCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <FilePreviewWidget payload={card.payload} />
    </CardShell>
  );
}
