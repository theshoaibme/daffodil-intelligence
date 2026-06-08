import { Loader2 } from "lucide-react";
import type { ParallelSimulationState } from "./parallelSimulator";

interface SimulatorPanelProps {
  simulation: ParallelSimulationState;
}

export function SimulatorPanel({ simulation }: SimulatorPanelProps) {
  const { tasks, pipelineLabel, modelTask } = simulation;
  if (tasks.length === 0) return null;

  return (
    <div className="absolute bottom-4 left-4 z-20 w-80 max-h-52 overflow-hidden rounded-2xl bg-surface-container-lowest/95 shadow-lg backdrop-blur-sm">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-outline-variant/15">
        <Loader2 size={14} className="animate-spin text-primary" />
        <div className="min-w-0">
          <p className="text-xs font-semibold text-on-surface">Real-time simulation</p>
          <p className="text-[10px] text-on-surface-variant/70 truncate">{pipelineLabel}</p>
        </div>
      </div>

      {modelTask && (
        <p className="px-4 py-2 text-[10px] text-primary/90 border-b border-outline-variant/10 leading-snug">
          {modelTask}
        </p>
      )}

      <ul className="overflow-y-auto max-h-32 px-3 py-2 space-y-1.5">
        {tasks.map((task) => (
          <li
            key={task.agentId}
            className="px-2.5 py-2 rounded-xl bg-surface-container-low text-[11px] leading-snug"
          >
            <span className="font-semibold text-on-surface">{task.agentName}</span>
            <span className="text-on-surface-variant/80"> — {task.task}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
