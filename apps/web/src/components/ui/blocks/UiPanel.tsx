import type { ReactNode } from "react";

interface UiPanelProps {
  title?: string | null;
  children: ReactNode;
  className?: string;
}

export function UiPanel({ title, children, className = "" }: UiPanelProps) {
  return (
    <div
      className={`bg-surface-container-high/30 rounded-lg overflow-hidden ${className}`}
    >
      {title ? (
        <div className="px-3 py-1.5">
          <h4 className="text-sm font-medium text-on-surface">{title}</h4>
        </div>
      ) : null}
      <div className="px-3 pb-3 pt-0">{children}</div>
    </div>
  );
}
