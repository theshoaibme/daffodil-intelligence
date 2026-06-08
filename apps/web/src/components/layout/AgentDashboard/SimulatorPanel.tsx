import { Loader2 } from "lucide-react";
import type { ParallelTask } from "./parallelSimulator";

interface SimulatorPanelProps {
  tasks: ParallelTask[];
  activeInputLabel: string;
}

export function SimulatorPanel({ tasks, activeInputLabel }: SimulatorPanelProps) {
  if (tasks.length === 0) return null;

  return (
    <div className="absolute bottom-4 left-4 z-20 w-72 max-h-48 overflow-hidden rounded-2xl bg-surface-container-lowest/95 shadow-lg backdrop-blur-sm">
      <div className="flex items-center gap-2 px-4 py-2.5">
        <Loader2 size={14} className="animate-spin text-primary" />
        <div className="min-w-0">
          <p className="text-xs font-semibold text-on-surface">Parallel simulation</p>
          <p className="text-[10px] text-on-surface-variant/70 truncate">via {activeInputLabel}</p>
        </div>
      </div>

      <ul className="overflow-y-auto max-h-32 px-3 pb-3 space-y-1.5">
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
