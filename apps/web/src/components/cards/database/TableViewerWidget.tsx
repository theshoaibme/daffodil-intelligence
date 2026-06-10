interface TableViewerWidgetProps {
  payload: Record<string, unknown>;
}

export function TableViewerWidget({ payload }: TableViewerWidgetProps) {
  const block = payload.block as Record<string, unknown> | undefined;
  const data = (block?.data ?? payload.data ?? payload) as Record<string, unknown>;
  const columns = (data.columns as Array<{ key: string; label: string }>) ?? [];
  const rows = (data.rows as Array<Record<string, unknown>>) ?? [];

  if (!columns.length && !rows.length) {
    return <p className="text-sm text-on-surface-variant">No table data</p>;
  }

  const keys = columns.length ? columns.map((c) => c.key) : Object.keys(rows[0] ?? {});

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            {keys.map((k) => (
              <th key={k} className="text-left p-2 border-b border-outline-variant/30 font-medium">
                {columns.find((c) => c.key === k)?.label ?? k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {keys.map((k) => (
                <td key={k} className="p-2 border-b border-outline-variant/10 text-on-surface-variant">
                  {String(row[k] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
