import { useEffect, useRef, type RefObject } from "react";

export function useAutoScroll(
  containerRef: RefObject<HTMLElement | null>,
  deps: unknown[]
) {
  const pinnedRef = useRef(true);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const onScroll = () => {
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
      pinnedRef.current = dist < 80;
    };

    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [containerRef]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !pinnedRef.current) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, deps);

  return {
    scrollToBottom: () => {
      const el = containerRef.current;
      if (!el) return;
      pinnedRef.current = true;
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    },
    isPinned: () => pinnedRef.current,
  };
}
