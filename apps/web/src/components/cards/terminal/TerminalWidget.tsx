interface TerminalWidgetProps {
  payload: Record<string, unknown>;
}

export function TerminalWidget({ payload }: TerminalWidgetProps) {
  const output = String(payload.output ?? payload.result ?? payload.stdout ?? "");
  const command = String(payload.command ?? payload.input_summary ?? "");

  return (
    <div className="font-mono text-xs">
      {command ? (
        <p className="text-primary mb-2">
          <span className="text-on-surface-variant">$</span> {command}
        </p>
      ) : null}
      <pre className="whitespace-pre-wrap text-on-surface bg-surface-container-high/50 rounded-lg px-3 py-2.5 max-h-48 overflow-y-auto">
        {output || "Running…"}
      </pre>
    </div>
  );
}
