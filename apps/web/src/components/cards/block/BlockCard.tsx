import { StructuredBlockRenderer } from "../../ui/blocks/StructuredBlockRenderer";
import { coerceUiBlock } from "../../../lib/uiBlocks/coerce";
import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function BlockCard({ card }: { card: Card }) {
  const raw = card.payload.block;
  const block = raw ? coerceUiBlock(raw as Record<string, unknown>) : null;

  return (
    <CardShell card={card}>
      {block ? <StructuredBlockRenderer blocks={[block]} /> : (
        <p className="text-sm text-on-surface-variant">Unable to display block</p>
      )}
    </CardShell>
  );
}
