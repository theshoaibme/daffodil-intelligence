import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { ImageGalleryWidget } from "./ImageGalleryWidget";

export default function ImageCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <ImageGalleryWidget payload={card.payload} />
    </CardShell>
  );
}
