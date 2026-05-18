import React from "react";

export function DropdownItem({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-container-highest transition-colors text-on-surface group text-left">
      {icon}
      <span className="text-sm font-medium">{text}</span>
    </button>
  );
}
