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
      void fitView(FLOW_FIT_OPTIONS);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [trigger, fitView]);

  return null;
}
