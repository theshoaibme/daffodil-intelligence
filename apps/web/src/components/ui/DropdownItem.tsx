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
      onClick={onClick}
      className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-surface-container-highest transition-colors text-on-surface group text-left cursor-pointer border-0 outline-none"
    >
      <div className="flex items-center gap-3">
        {icon}
        <span className="text-sm font-medium">{text}</span>
      </div>
      {active && <Check size={16} className="text-primary" />}
    </button>
  );
}
