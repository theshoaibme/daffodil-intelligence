export type LogoSize = "sm" | "md" | "lg";

const SIZE_CLASSES: Record<LogoSize, { title: string; subtitle: string; subtitleOffset: string }> = {
  sm: {
    title: "text-lg sm:text-xl",
    subtitle: "text-[9px] sm:text-[10px]",
    subtitleOffset: "-mt-1",
  },
  md: {
    title: "text-xl sm:text-2xl",
    subtitle: "text-[10px] sm:text-xs",
    subtitleOffset: "-mt-1",
  },
  lg: {
    title: "text-2xl sm:text-3xl",
    subtitle: "text-xs sm:text-sm",
    subtitleOffset: "-mt-1.5",
  },
};

export interface LogoProps {
  size?: LogoSize;
  className?: string;
}

export function Logo({ size = "sm", className = "" }: LogoProps) {
  const styles = SIZE_CLASSES[size];

  return (
    <span className={`flex flex-col leading-none min-w-0 ${className}`}>
      <span className={`${styles.title} font-bold text-primary tracking-tight truncate`}>
        Daffodil
      </span>
      <span
        className={`${styles.subtitle} ${styles.subtitleOffset} italic font-medium text-on-surface-variant tracking-wide truncate`}
      >
        Intelligence
      </span>
    </span>
  );
}
