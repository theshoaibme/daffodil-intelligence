export const BOTTOM_BAR_LAYOUT_ID = "bottom-mode-bar";

export const modeSpring = {
  type: "spring" as const,
  stiffness: 400,
  damping: 34,
  mass: 0.85,
};

export const modeSpringSoft = {
  type: "spring" as const,
  stiffness: 320,
  damping: 30,
  mass: 0.9,
};

export const overlayFade = {
  duration: 0.28,
  ease: [0.4, 0, 0.2, 1] as const,
};

/** Sidebar width — smooth tween without spring bounce. */
export const sidebarWidthTransition = {
  duration: 0.24,
  ease: [0.4, 0, 0.2, 1] as const,
};

export const sidebarPanelTransition = {
  duration: 0.18,
  ease: [0.4, 0, 0.2, 1] as const,
};

/** Dropdown panel — spring open, quick ease close (no popLayout bounce). */
export const dropdownPanelVariants = {
  hidden: {
    opacity: 0,
    scale: 0.94,
    y: -10,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: "spring" as const,
      stiffness: 480,
      damping: 36,
      mass: 0.72,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    y: -6,
    transition: {
      duration: 0.14,
      ease: [0.4, 0, 1, 1] as const,
    },
  },
};

/** Skip enter animation on reload; run it once UI hydration is ready. */
export function enterOrSkip<T>(ready: boolean, enter: T): T | false {
  return ready ? enter : false;
}
