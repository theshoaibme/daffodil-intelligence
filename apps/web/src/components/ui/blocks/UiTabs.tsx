import { useState, type ReactNode } from "react";

export interface UiTabItem {
  id: string;
  label: string;
  content: ReactNode;
}

interface UiTabsProps {
  tabs: UiTabItem[];
}

export function UiTabs({ tabs }: UiTabsProps) {
  const [active, setActive] = useState(tabs[0]?.id ?? "");

  if (!tabs.length) return null;

  const current = tabs.find((t) => t.id === active) ?? tabs[0];

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1 border-b border-outline-variant/40 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActive(tab.id)}
            className={`px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
              tab.id === current.id
                ? "text-on-surface border-b-2 border-primary -mb-px"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div>{current.content}</div>
    </div>
  );
}
