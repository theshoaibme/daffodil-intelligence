import React from 'react';
import { Palette } from 'lucide-react';

const ColorPalette: React.FC = () => {
  return (
    <div className="h-full bg-surface-container rounded-lg p-6 border-0 shadow-none flex flex-col justify-between">
      <div className="border-0 shadow-none">
        <div className="flex flex-row items-center space-x-3 mb-4 border-0 shadow-none">
          <Palette size={24} className="text-primary" />
          <h2 className="text-xl font-bold tracking-tight">Dynamic Palette</h2>
        </div>
        <p className="text-[14px] text-on-surface-variant font-medium mb-8">
          Colors are derived from the central design tokens with zero borders and zero shadows.
        </p>
        <div className="space-y-4 border-0 shadow-none">
          <div className="p-5 rounded-md bg-primary text-on-primary font-bold text-[14px]">
            Primary Brand Color
          </div>
          <div className="p-5 rounded-md bg-surface-lowest text-on-surface font-bold text-[14px]">
            Surface Layer
          </div>
          <div className="p-5 rounded-md bg-secondary text-on-primary font-bold text-[14px]">
            Secondary Accent
          </div>
        </div>
      </div>
    </div>
  );
};

export default ColorPalette;
