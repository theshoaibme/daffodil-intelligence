import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const UiAnimationContext = createContext(false);

export function UiAnimationProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <UiAnimationContext.Provider value={ready}>{children}</UiAnimationContext.Provider>
  );
}

/** False on first paint (restored state), true after hydration (user toggles animate). */
export function useUiAnimationReady() {
  return useContext(UiAnimationContext);
}
