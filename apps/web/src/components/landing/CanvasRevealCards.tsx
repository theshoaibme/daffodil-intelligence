import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  Bot,
  FileText,
  GraduationCap,
  MessageSquare,
  Network,
} from "lucide-react";
import { CanvasRevealEffect } from "@components/ui/canvas-reveal-effect";

type RevealCardConfig = {
  title: string;
  description: string;
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
    description: "CGPA, courses, assignments, and exam prep — guided by AI.",
    icon: GraduationCap,
    animationSpeed: 5.1,
    containerClassName: "bg-emerald-900",
    colors: [[16, 185, 129]],
  },
  {
    title: "Research library",
    description: "10,000+ papers with PDFs across every major field.",
    icon: FileText,
    animationSpeed: 3.2,
    containerClassName: "bg-violet-950",
    colors: [
      [139, 92, 246],
      [167, 139, 250],
    ],
    dotSize: 2,
  },
  {
    title: "Academic network",
    description: "Connect with professors, universities, and research groups.",
    icon: Network,
    animationSpeed: 3,
    containerClassName: "bg-black",
    colors: [
      [66, 89, 255],
      [232, 121, 249],
    ],
    dotSize: 2,
    overlay: true,
  },
  {
    title: "Multi-agent studio",
    description: "Specialized agents for coding, campus ops, and automation.",
    icon: Bot,
    animationSpeed: 4,
    containerClassName: "bg-sky-700",
    colors: [[56, 189, 248]],
  },
  {
    title: "Campus services",
    description: "Shuttle, fees, schedules, and DIU-specific answers.",
    icon: BookOpen,
    animationSpeed: 3.5,
    containerClassName: "bg-amber-900",
    colors: [[251, 191, 36]],
  },
  {
    title: "Live voice & chat",
    description: "Talk or type — real-time help whenever you need it.",
    icon: MessageSquare,
    animationSpeed: 3,
    containerClassName: "bg-sky-600",
    colors: [[125, 211, 252]],
  },
];

export function CanvasRevealCards() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 lg:gap-8">
      {cards.map((card) => (
        <RevealCard key={card.title} {...card} />
      ))}
    </div>
  );
}

function RevealCard({
  title,
  description,
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
      className="group/canvas-card relative mx-auto flex h-[30rem] w-full max-w-sm items-center justify-center overflow-hidden p-4"
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

      <div className="relative z-20 px-2">
        <div className="mx-auto flex w-full items-center justify-center text-center transition duration-200 group-hover/canvas-card:-translate-y-4 group-hover/canvas-card:opacity-0">
          <div className="flex h-14 w-14 items-center justify-center bg-primary/10 sm:h-16 sm:w-16">
            <Icon className="h-7 w-7 text-primary sm:h-8 sm:w-8" />
          </div>
        </div>
        <h3 className="relative z-10 mt-4 text-center text-lg font-bold text-on-surface opacity-0 transition duration-200 group-hover/canvas-card:-translate-y-2 group-hover/canvas-card:text-white group-hover/canvas-card:opacity-100 sm:text-xl">
          {title}
        </h3>
        <p className="relative z-10 mt-2 text-center text-sm text-on-surface-variant opacity-0 transition duration-200 delay-75 group-hover/canvas-card:text-white/90 group-hover/canvas-card:opacity-100">
          {description}
        </p>
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

export function CanvasRevealFeatureIcon() {
  return (
    <svg
      width="66"
      height="65"
      viewBox="0 0 66 65"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="h-10 w-10 text-on-surface group-hover/canvas-card:text-white"
    >
      <path
        d="M8 8.05571C8 8.05571 54.9009 18.1782 57.8687 30.062C60.8365 41.9458 9.05432 57.4696 9.05432 57.4696"
        stroke="currentColor"
        strokeWidth="15"
        strokeMiterlimit="3.86874"
        strokeLinecap="round"
        style={{ mixBlendMode: "darken" }}
      />
    </svg>
  );
}
