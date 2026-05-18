import React from "react";

export function HeaderIcon({ title, icon }: { title: string; icon: React.ReactNode }) {
  return (
    <button className="p-2 hover:bg-surface-container-high rounded-lg text-on-surface-variant hover:text-on-surface transition-colors flex items-center justify-center" title={title}>
      {icon}
    </button>
  );
}
