interface GenericResultWidgetProps {
  payload: Record<string, unknown>;
}

export function GenericResultWidget({ payload }: GenericResultWidgetProps) {
  const message = payload.message ?? payload.summary ?? payload.result ?? payload.content;
  if (typeof message === "string" && message) {
    return <p className="text-sm text-on-surface whitespace-pre-wrap">{message}</p>;
  }
  if (payload.data) {
    return (
      <pre className="text-xs overflow-x-auto rounded-lg bg-surface-container-high/50 px-3 py-2.5">
        {JSON.stringify(payload.data, null, 2)}
      </pre>
    );
  }
  return <p className="text-sm text-on-surface-variant">Result pending…</p>;
}
