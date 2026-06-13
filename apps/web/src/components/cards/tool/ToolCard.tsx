import { resolveToolRenderer } from "../../../engine/registries/ToolRendererRegistry";
import { resolveWidget } from "../../../engine/registries/WidgetRegistry";
import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function ToolCard({ card }: { card: Card }) {
  const toolName = String(card.payload.tool_name ?? card.payload.name ?? "");
  const renderer = resolveToolRenderer(toolName, card.source.mcp_server);
  const Widget = resolveWidget(renderer.widget_type);

  return (
    <CardShell card={card}>
      {card.payload.input_summary ? (
        <p className="text-xs text-on-surface-variant mb-2">{String(card.payload.input_summary)}</p>
      ) : null}
      <Widget payload={card.payload} />
    </CardShell>
  );
}
