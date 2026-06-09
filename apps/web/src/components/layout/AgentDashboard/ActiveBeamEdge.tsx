import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";

export function ActiveBeamEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps) {
  const active = Boolean(data?.active);
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        style={{
          stroke: active ? "#4259ff" : "#c5c5d9",
          strokeWidth: active ? 2.5 : 1.75,
          opacity: active ? 1 : 0.85,
        }}
      />
      {active && path && (
        <>
          <circle r="5" fill="#4259ff" opacity="0.35">
            <animateMotion dur="1.4s" repeatCount="indefinite" path={path} />
          </circle>
          <circle r="3" fill="#ff6b2c">
            <animateMotion dur="1.4s" repeatCount="indefinite" path={path} />
          </circle>
        </>
      )}
    </>
  );
}
