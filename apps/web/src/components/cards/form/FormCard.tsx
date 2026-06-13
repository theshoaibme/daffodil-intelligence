import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";

export default function FormCard({ card }: { card: Card }) {
  const fields = (card.payload.fields as Array<{ name: string; label: string; type?: string }>) ?? [];

  return (
    <CardShell card={card}>
      <form className="space-y-3" onSubmit={(e) => e.preventDefault()}>
        {fields.map((f) => (
          <label key={f.name} className="block text-sm">
            <span className="text-on-surface-variant text-xs">{f.label}</span>
            <input
              name={f.name}
              type={f.type ?? "text"}
              className="mt-1 w-full rounded-lg border border-outline-variant/40 bg-surface px-3 py-2 text-sm"
            />
          </label>
        ))}
        <button type="submit" className="px-3 py-1.5 text-xs rounded-lg bg-primary text-on-primary">
          Submit
        </button>
      </form>
    </CardShell>
  );
}
