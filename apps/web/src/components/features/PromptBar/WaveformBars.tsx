interface WaveformBarsProps {
  levels: number[];
  animated?: boolean;
  className?: string;
}

export function WaveformBars({ levels, animated = false, className = "" }: WaveformBarsProps) {
  return (
    <div className={`flex items-center gap-[3px] h-4 ${className}`} aria-hidden>
      {levels.map((level, i) => (
        <span
          key={i}
          className={`w-[3px] rounded-full bg-on-surface-variant/80 ${
            animated ? "transition-[height] duration-75 ease-out" : ""
          }`}
          style={{ height: `${Math.round(6 + level * 10)}px` }}
        />
      ))}
    </div>
  );
}
