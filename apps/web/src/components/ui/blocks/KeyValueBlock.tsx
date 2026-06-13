import { UiPanel } from "./UiPanel";

interface KeyValueBlockProps {
  title?: string;
  rows: Array<{ key: string; value: string }>;
}

export function KeyValueBlock({ title, rows }: KeyValueBlockProps) {
  return (
    <UiPanel title={title}>
      <dl className="flex flex-col gap-1.5">
        {rows.map((row, idx) => (
          <div key={`${row.key}-${idx}`} className="grid grid-cols-[minmax(0,35%)_1fr] gap-2 text-xs">
            <dt className="text-on-surface-variant font-medium truncate">{row.key}</dt>
            <dd className="text-on-surface break-words">{row.value}</dd>
          </div>
        ))}
      </dl>
    </UiPanel>
  );
}
