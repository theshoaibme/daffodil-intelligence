import React from "react";
import { Check } from "lucide-react";

interface DropdownItemProps {
  icon: React.ReactNode;
  text: string;
  onClick?: () => void;
  active?: boolean;
}

export function DropdownItem({ icon, text, onClick, active }: DropdownItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative w-full flex items-center justify-between pl-2.5 pr-8 py-2 rounded-lg transition-colors text-left cursor-pointer border-0 outline-none ${
        active
          ? "bg-surface-container-highest text-on-surface"
          : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
      }`}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="shrink-0 text-on-surface-variant [&>svg]:size-4">{icon}</span>
        <span className="text-sm font-normal truncate">{text}</span>
      </div>
      {active && (
        <span
          className="absolute right-2 flex h-3.5 w-3.5 items-center justify-center text-on-surface"
          aria-hidden
        >
          <Check className="h-4 w-4" strokeWidth={2} />
        </span>
      )}
    </button>
  );
}
