interface CodeViewerWidgetProps {
  payload: Record<string, unknown>;
}

export function CodeViewerWidget({ payload }: CodeViewerWidgetProps) {
  const code = String(payload.code ?? payload.content ?? payload.result ?? "");
  const lang = String(payload.lang ?? payload.language ?? "text");

  if (!code) return <p className="text-sm text-on-surface-variant">No code output</p>;

  return (
    <pre className="text-xs overflow-x-auto rounded-lg bg-surface-container-high/50 px-3 py-2.5">
      <code className={`language-${lang}`}>{code}</code>
    </pre>
  );
}
