import type { UiTableColumn } from "@lib/uiBlocks/types";

interface UiDataTableProps {
  columns: UiTableColumn[];
  rows: Record<string, unknown>[];
  compact?: boolean;
}

export function UiDataTable({ columns, rows, compact = true }: UiDataTableProps) {
  if (!rows.length) {
    return <p className="text-sm text-on-surface-variant">No rows.</p>;
  }

  const cellClass = compact ? "px-2 py-1.5 text-xs" : "px-3 py-2 text-sm";

  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full min-w-[280px] border-collapse">
        <thead>
          <tr className="border-b border-outline-variant/40">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`${cellClass} text-left font-semibold text-on-surface-variant sticky top-0 bg-surface-container-high/80`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-outline-variant/20 last:border-0">
              {columns.map((col) => (
                <td key={col.key} className={`${cellClass} text-on-surface`}>
                  {formatCell(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
