interface SearchResultsWidgetProps {
  payload: Record<string, unknown>;
}

export function SearchResultsWidget({ payload }: SearchResultsWidgetProps) {
  const results = (payload.results as Array<{ title?: string; url?: string; snippet?: string }>) ?? [];
  const query = String(payload.query ?? payload.input_summary ?? "");

  if (!results.length && !query) {
    return <p className="text-sm text-on-surface-variant">Searching…</p>;
  }

  return (
    <div className="space-y-2">
      {query ? <p className="text-xs text-on-surface-variant">Query: {query}</p> : null}
      {results.map((r, i) => (
        <div key={i} className="rounded-lg bg-surface-container-high/30 px-2.5 py-2">
          {r.url ? (
            <a
              href={r.url}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-medium text-primary hover:underline"
            >
              {r.title ?? r.url}
            </a>
          ) : (
            <p className="text-sm font-medium">{r.title}</p>
          )}
          {r.snippet ? <p className="text-xs text-on-surface-variant mt-1">{r.snippet}</p> : null}
        </div>
      ))}
    </div>
  );
}
