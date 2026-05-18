import React from 'react';

interface LoaderProps {
  variant?: 'spinner' | 'dots' | 'linear'; // Added 'linear' variant for horizontal sliding progress bar
  diameter?: number;
  strokeWidth?: number;
  color?: 'primary' | 'secondary' | 'error'; // Added robust color variants
  message?: string;
  fullPage?: boolean;
  overlay?: boolean;
}

export const Loader: React.FC<LoaderProps> = ({
  variant = 'spinner',
  diameter = 40,
  strokeWidth = 4,
  color = 'primary',
  message,
  fullPage = false,
  overlay = false,
}) => {
  // Container styling based on fullPage and overlay
  const containerClasses = React.useMemo(() => {
    const base = 'flex flex-col items-center justify-center border-0 shadow-none transform-none transition-none';
    if (fullPage) {
      return `${base} fixed inset-0 z-[9999] bg-[#213be7]/[0.06] dark:bg-[#0E0E10]/80 backdrop-blur-md`;
    }
    if (overlay) {
      return `${base} absolute inset-0 z-50 rounded-inherit bg-[#213be7]/[0.06] dark:bg-[#161618]/80 backdrop-blur-[4px]`;
    }
    return base;
  }, [fullPage, overlay]);

  // Color mapping utility for SVGs and dots
  const colorHex = React.useMemo(() => {
    if (color === 'secondary') return 'var(--color-secondary)';
    if (color === 'error') return 'var(--color-error)';
    return 'var(--color-primary)';
  }, [color]);

  return (
    <div className={containerClasses}>
      {variant === 'spinner' ? (
        <div 
          className="relative flex items-center justify-center border-0 shadow-none"
          style={{ width: diameter, height: diameter }}
        >
          {/* Background Track SVG */}
          <svg className="absolute inset-0 w-full h-full border-0">
            <circle
              cx={diameter / 2}
              cy={diameter / 2}
              r={(diameter - strokeWidth) / 2}
              fill="none"
              stroke="rgba(33, 59, 231, 0.08)"
              strokeWidth={strokeWidth}
              className="border-0"
            />
          </svg>

          {/* Rotating Arc SVG */}
          <svg className="absolute inset-0 w-full h-full animate-google-rotate border-0">
            <circle
              cx={diameter / 2}
              cy={diameter / 2}
              r={(diameter - strokeWidth) / 2}
              fill="none"
              stroke={colorHex}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              className="animate-google-dash border-0"
            />
          </svg>
        </div>
      ) : variant === 'dots' ? (
        /* Dots Variant */
        <div className="flex flex-row space-x-2 justify-center items-center">
          {color === 'primary' ? (
            // Traditional Multi-color Google dots
            ['#4285F4', '#EA4335', '#FBBC05', '#34A853'].map((dotColor) => (
              <div
                key={dotColor}
                className="rounded-full border-0 shadow-none animate-pulse"
                style={{
                  width: diameter * 0.3,
                  height: diameter * 0.3,
                  backgroundColor: dotColor,
                }}
              />
            ))
          ) : (
            // Monochromatic themed dots
            [1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="rounded-full border-0 shadow-none animate-pulse"
                style={{
                  width: diameter * 0.3,
                  height: diameter * 0.3,
                  backgroundColor: colorHex,
                  animationDelay: `${i * 0.2}s`,
                }}
              />
            ))
          )}
        </div>
      ) : (
        /* Linear Google-style running progress bar variant */
        <div className="w-64 h-1 bg-primary/10 rounded-full overflow-hidden relative border-0 shadow-none">
          <div 
            className="h-full rounded-full absolute top-0 animate-linear-loader"
            style={{ 
              width: '40%',
              backgroundColor: colorHex
            }}
          />
        </div>
      )}
      {message && (
        <p className="text-[14px] text-on-surface-variant/80 mt-3 font-medium">
          {message}
        </p>
      )}
    </div>
  );
};
