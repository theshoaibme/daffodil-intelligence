import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function AgentCard({ card }: { card: Card }) {
  const p = card.payload;
  const tools = (p.tools_active as string[]) ?? [];
  const log = (p.log_tail as string[]) ?? [];

  return (
    <CardShell card={card}>
      <div className="space-y-2 text-sm">
        {p.current_action ? (
          <p className="text-on-surface-variant">{String(p.current_action)}</p>
        ) : null}
        {typeof p.progress === "number" ? (
          <div className="h-1.5 rounded-full bg-outline-variant/20 overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${Math.round(Number(p.progress) * 100)}%` }}
            />
          </div>
        ) : null}
        {tools.length > 0 ? (
          <p className="text-xs text-on-surface-variant">Tools: {tools.join(", ")}</p>
        ) : null}
        {p.thought_preview ? (
          <p className="text-xs italic text-on-surface-variant/80">{String(p.thought_preview)}</p>
        ) : null}
        {log.length > 0 ? (
          <ul className="text-xs text-on-surface-variant space-y-0.5">
            {log.slice(-4).map((line, i) => (
              <li key={i}>• {line}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </CardShell>
  );
}
