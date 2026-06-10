interface BrowserSessionWidgetProps {
  payload: Record<string, unknown>;
}

export function BrowserSessionWidget({ payload }: BrowserSessionWidgetProps) {
  const url = String(payload.url ?? "");
  const screenshot = String(payload.screenshot_url ?? "");

  return (
    <div className="space-y-2">
      {url ? (
        <a href={url} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline break-all">
          {url}
        </a>
      ) : (
        <p className="text-sm text-on-surface-variant">Browser session active…</p>
      )}
      {screenshot ? (
        <img src={screenshot} alt="Browser frame" className="rounded-lg max-h-48 object-cover w-full" />
      ) : null}
    </div>
  );
}
