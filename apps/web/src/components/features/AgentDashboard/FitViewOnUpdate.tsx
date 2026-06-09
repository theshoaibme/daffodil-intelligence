import { useEffect } from "react";
import { useReactFlow } from "@xyflow/react";
import { FLOW_FIT_OPTIONS } from "./flowLayout";

interface FitViewOnUpdateProps {
  trigger: number;
}

export function FitViewOnUpdate({ trigger }: FitViewOnUpdateProps) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (trigger === 0) return;
    const frame = window.requestAnimationFrame(() => {
      // First fit: snap instantly so load does not animate from a stale viewport.
      const options =
        trigger === 1
          ? { ...FLOW_FIT_OPTIONS, duration: 0 }
          : FLOW_FIT_OPTIONS;
      void fitView(options);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [trigger, fitView]);

  return null;
}
