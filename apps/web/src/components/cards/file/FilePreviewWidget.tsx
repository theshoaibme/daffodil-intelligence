interface FilePreviewWidgetProps {
  payload: Record<string, unknown>;
}

export function FilePreviewWidget({ payload }: FilePreviewWidgetProps) {
  const name = String(payload.name ?? payload.file_path ?? "file");
  const url = payload.url ? String(payload.url) : null;
  const mime = String(payload.mime ?? "");

  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-lg">📄</div>
      <div className="min-w-0">
        {url ? (
          <a href={url} target="_blank" rel="noreferrer" className="text-sm font-medium text-primary hover:underline truncate block">
            {name}
          </a>
        ) : (
          <p className="text-sm font-medium truncate">{name}</p>
        )}
        {mime ? <p className="text-xs text-on-surface-variant">{mime}</p> : null}
      </div>
    </div>
  );
}
