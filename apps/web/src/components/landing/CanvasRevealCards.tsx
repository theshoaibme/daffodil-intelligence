import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BookOpen, Bot, GraduationCap } from "lucide-react";
import { CanvasRevealEffect } from "@components/ui/canvas-reveal-effect";

type RevealCardConfig = {
  title: string;
  icon: typeof GraduationCap;
  animationSpeed: number;
  containerClassName: string;
  colors: number[][];
  dotSize?: number;
  overlay?: boolean;
};

const cards: RevealCardConfig[] = [
  {
    title: "Study smarter",
    icon: GraduationCap,
    animationSpeed: 5.1,
    containerClassName: "bg-emerald-900",
    colors: [[16, 185, 129]],
  },
  {
    title: "Campus connected",
    icon: BookOpen,
    animationSpeed: 3,
    containerClassName: "bg-black",
    colors: [
      [66, 89, 255],
      [125, 211, 252],
    ],
    dotSize: 2,
    overlay: true,
  },
  {
    title: "AI-powered help",
    icon: Bot,
    animationSpeed: 3,
    containerClassName: "bg-sky-600",
    colors: [[125, 211, 252]],
  },
];

export function CanvasRevealCards() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 lg:flex-row lg:gap-8">
      {cards.map((card) => (
        <RevealCard key={card.title} {...card} />
      ))}
    </div>
  );
}

function RevealCard({
  title,
  icon: Icon,
  animationSpeed,
  containerClassName,
  colors,
  dotSize,
  overlay,
}: RevealCardConfig) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group/canvas-card relative mx-auto flex h-[22rem] w-full max-w-sm items-center justify-center border border-outline-variant/40 p-4 sm:h-[26rem]"
    >
      <CornerIcon className="absolute -left-3 -top-3 h-6 w-6 text-on-surface" />
      <CornerIcon className="absolute -bottom-3 -left-3 h-6 w-6 text-on-surface" />
      <CornerIcon className="absolute -right-3 -top-3 h-6 w-6 text-on-surface" />
      <CornerIcon className="absolute -bottom-3 -right-3 h-6 w-6 text-on-surface" />

      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 h-full w-full"
          >
            <CanvasRevealEffect
              animationSpeed={animationSpeed}
              containerClassName={containerClassName}
              colors={colors}
              dotSize={dotSize}
            />
            {overlay && (
              <div className="absolute inset-0 bg-black/50 [mask-image:radial-gradient(400px_at_center,white,transparent)] dark:bg-black/90" />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative z-20">
        <div className="mx-auto flex w-full items-center justify-center text-center transition duration-200 group-hover/canvas-card:-translate-y-4 group-hover/canvas-card:opacity-0">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <Icon className="h-8 w-8 text-primary" />
          </div>
        </div>
        <h3 className="relative z-10 mt-4 text-center text-xl font-bold text-on-surface opacity-0 transition duration-200 group-hover/canvas-card:-translate-y-2 group-hover/canvas-card:text-white group-hover/canvas-card:opacity-100">
          {title}
        </h3>
      </div>
    </div>
  );
}

function CornerIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth="1.5"
      stroke="currentColor"
      className={className}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m6-6H6" />
    </svg>
  );
}
