import React from 'react';
import { Type } from 'lucide-react';

const TypographyShowcase: React.FC = () => {
  return (
    <div className="h-full bg-surface-container rounded-lg p-6 border-0 shadow-none">
      <div className="flex flex-row items-center space-x-3 mb-4 border-0 shadow-none">
        <Type size={24} className="text-primary" />
        <h2 className="text-xl font-bold tracking-tight">Typography</h2>
      </div>
      <p className="text-[14px] text-on-surface-variant font-medium mb-8">
        Switching themes changes the entire font family instantly. No transitions.
      </p>
      <div className="space-y-6 border-0 shadow-none">
        <div>
          <span className="text-[11px] uppercase tracking-wider text-on-surface-variant/60 font-semibold block mb-1">Display Large</span>
          <h3 className="text-5xl font-extrabold tracking-tight">Heading 1</h3>
        </div>
        <div>
          <span className="text-[11px] uppercase tracking-wider text-on-surface-variant/60 font-semibold block mb-1">Headline Medium</span>
          <h4 className="text-2xl font-bold tracking-tight">Subheading</h4>
        </div>
        <div>
          <span className="text-[11px] uppercase tracking-wider text-on-surface-variant/60 font-semibold block mb-1">Body Large</span>
          <p className="text-[15px] leading-relaxed">
            The quick brown fox jumps over the lazy dog.
          </p>
        </div>
        <div>
          <span className="text-[11px] uppercase tracking-wider text-on-surface-variant/60 font-semibold block mb-2">Technical Label</span>
          <code className="text-[12px] font-mono text-primary bg-surface-highest/50 px-2 py-1 rounded-sm inline-block">
            JetBrains Mono for technical data
          </code>
        </div>
      </div>
    </div>
  );
};

export default TypographyShowcase;
