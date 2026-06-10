import type { ReactNode } from "react";

interface UiPanelProps {
  title?: string | null;
  children: ReactNode;
  className?: string;
}

export function UiPanel({ title, children, className = "" }: UiPanelProps) {
  return (
    <div
      className={`glass-gradient-panel border border-outline-variant/40 rounded-2xl overflow-hidden ${className}`}
    >
      {title ? (
        <div className="px-3 py-2 border-b border-outline-variant/30 bg-surface-container-high/40">
          <h4 className="text-sm font-semibold text-on-surface">{title}</h4>
        </div>
      ) : null}
      <div className="p-3">{children}</div>
    </div>
  );
}
