import { useEffect, useState } from "react";

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false
  );

  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = () => setMatches(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}

/** Tailwind `md` — tablet+ layout with side response rail. */
export function useIsMdUp(): boolean {
  return useMediaQuery("(min-width: 768px)");
}

/** Tailwind `lg` — desktop layout with persistent sidebar rail. */
export function useIsLgUp(): boolean {
  return useMediaQuery("(min-width: 1024px)");
}
