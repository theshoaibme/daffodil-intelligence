import React from 'react';

interface TooltipProps {
  title: string;
  children: React.ReactNode;
}

export const Tooltip: React.FC<TooltipProps> = ({ title, children }) => {
  return (
    <div className="relative group inline-block">
      {children}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-[10px] font-medium text-[#f1f3f4] bg-[#202124] rounded-[4px] whitespace-nowrap shadow-none border-0 opacity-0 pointer-events-none group-hover:opacity-100 group-focus:opacity-100 transition-opacity duration-0 delay-500 z-[999]">
        {title}
      </div>
    </div>
  );
};
