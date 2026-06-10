import { useEffect, useMemo } from "react";
import {
  Compass,
  ChevronUp,
  ChevronDown,
  CheckCircle2,
  Circle,
  Bot,
  Wrench,
  Brain,
  AlertCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader } from "../../ui/Loader";
import { useLocalStorageState } from "@hooks";
import { enterOrSkip } from "@lib";
import type { TaskPanelItem } from "@lib";

export interface TaskItem {
  id: string;
  text: string;
  active?: boolean;
  depth?: number;
  parallelGroup?: string;
  kind?: TaskPanelItem["kind"];
  status?: TaskPanelItem["status"];
}

export interface TaskPanelProps {
  tasksCollapsed: boolean;
  setTasksCollapsed: (collapsed: boolean) => void;
  uiReady?: boolean;
  /** Live agent tasks — when set, overrides stored tasks and is not persisted. */
  liveTasks?: TaskItem[] | null;
  agentMode?: boolean;
}

export const initialTasks: TaskItem[] = [];

const INDENT_PX = 14;

function KindIcon({ kind }: { kind?: TaskPanelItem["kind"] }) {
  const className = "text-on-surface-variant/70 shrink-0";
  switch (kind) {
    case "agent":
      return <Bot size={14} className={className} />;
    case "tool":
      return <Wrench size={14} className={className} />;
    case "memory":
      return <Brain size={14} className={className} />;
    default:
      return <Circle size={8} className={`${className} fill-current`} />;
  }
}

function StatusIcon({
  active,
  status,
}: {
  active?: boolean;
  status?: TaskPanelItem["status"];
}) {
  if (active || status === "active") {
    return <Loader diameter={16} strokeWidth={2} color="primary" />;
  }
  if (status === "error") {
    return <AlertCircle size={16} className="text-error shrink-0" />;
  }
  if (status === "pending") {
    return <Circle size={14} className="text-on-surface-variant/40 shrink-0" />;
  }
  return <CheckCircle2 size={16} className="text-primary shrink-0" />;
}

export function LogItem({
  text,
  active = false,
  depth = 0,
  kind,
  status,
  onClick,
}: {
  text: string;
  active?: boolean;
  depth?: number;
  kind?: TaskPanelItem["kind"];
  status?: TaskPanelItem["status"];
  onClick?: () => void;
}) {
  const indent = Math.min(depth, 5) * INDENT_PX;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex w-full min-w-0 items-center gap-2 rounded-lg border px-2 py-1.5 text-left transition-all ${
        active
          ? "border-primary/35 bg-surface-container text-on-surface shadow-sm"
          : "border-outline-variant/25 bg-surface-container-highest/30 text-on-surface-variant hover:border-outline-variant/40 hover:bg-surface-container-highest/60 hover:text-on-surface"
      }`}
      style={{ paddingLeft: `${8 + indent}px` }}
    >
      {depth > 0 && (
        <span
          className="pointer-events-none absolute top-0 bottom-3 w-px bg-outline-variant/35"
          style={{ left: `${4 + indent - INDENT_PX / 2}px` }}
          aria-hidden
        />
      )}
      <div className="flex h-[18px] w-[18px] shrink-0 items-center justify-center">
        <StatusIcon active={active} status={status} />
      </div>
      <KindIcon kind={kind} />
      <span className="min-w-0 flex-1 truncate text-sm font-medium leading-snug">{text}</span>
    </button>
  );
}

const TASKS_STORAGE_KEY = "di-dashboard-task-items";

export function TaskPanel({
  tasksCollapsed,
  setTasksCollapsed,
  uiReady = true,
  liveTasks = null,
  agentMode = false,
}: TaskPanelProps) {
  const [storedTasks, setStoredTasks] = useLocalStorageState<TaskItem[]>(TASKS_STORAGE_KEY, initialTasks);
  const usingLiveTasks = agentMode;
  const tasks = usingLiveTasks ? (liveTasks ?? []) : storedTasks;
  const activeTask = tasks.find((t) => t.active);

  const panelMaxHeight = useMemo(() => {
    const rows = Math.max(tasks.length, 1);
    const estimated = 44 + rows * 40;
    return Math.min(Math.max(estimated, 120), 320);
  }, [tasks.length]);

  const handleTaskClick = (taskId: string) => {
    if (usingLiveTasks) return;
    setStoredTasks((prev) =>
      prev.map((t) => ({
        ...t,
        active: t.id === taskId,
      }))
    );
  };

  useEffect(() => {
    if (usingLiveTasks) return;
    setStoredTasks((prev) => {
      if (!prev.some((task) => task.active)) return prev;
      return prev.map((task) => ({ ...task, active: false }));
    });
  }, [setStoredTasks, usingLiveTasks]);

  return (
    <div
      className="flex w-full flex-col overflow-hidden rounded-3xl border border-outline-variant/40 glass-gradient-panel shadow-md"
      id="agent-log-panel"
    >
      <motion.div
        initial={false}
        animate={{ height: tasksCollapsed ? 56 : panelMaxHeight }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="flex flex-col justify-end overflow-hidden"
      >
        <AnimatePresence mode="wait">
          {tasksCollapsed ? (
            <motion.div
              key="collapsed"
              initial={enterOrSkip(uiReady, { opacity: 0, y: -5 })}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.2 }}
              className="flex h-[56px] items-center border-b border-outline-variant/20 p-2"
            >
              {activeTask ? (
                <LogItem
                  text={activeTask.text}
                  active
                  depth={activeTask.depth}
                  kind={activeTask.kind}
                  status={activeTask.status}
                  onClick={() => handleTaskClick(activeTask.id)}
                />
              ) : (
                <span className="w-full text-center text-xs font-medium text-on-surface-variant/50">
                  {agentMode ? "Waiting for agents…" : "No active tasks"}
                </span>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="expanded"
              initial={enterOrSkip(uiReady, { opacity: 0, y: 5 })}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              transition={{ duration: 0.2 }}
              className="custom-scrollbar flex min-h-[100px] w-full flex-col gap-1 overflow-y-auto p-2"
              style={{ maxHeight: panelMaxHeight - 4 }}
            >
              {tasks.length > 0 ? (
                tasks.map((task) => (
                  <LogItem
                    key={task.id}
                    text={task.text}
                    active={task.active}
                    depth={task.depth}
                    kind={task.kind}
                    status={task.status}
                    onClick={() => handleTaskClick(task.id)}
                  />
                ))
              ) : (
                <span className="py-6 text-center text-xs font-medium text-on-surface-variant/50">
                  {agentMode ? "Waiting for agents…" : "No tasks active"}
                </span>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <div className="flex items-center justify-between border-t border-outline-variant/20 bg-surface-container-highest/20 p-2.5 px-3">
        <div className="flex items-center gap-2">
          <Compass size={18} className="text-primary" />
          <span className="text-sm font-semibold text-on-surface">
            {agentMode ? "Agent tasks" : "Task"}
          </span>
          {tasks.length > 0 && (
            <span className="rounded-full bg-surface-container-highest px-1.5 py-0.5 text-[10px] font-medium text-on-surface-variant">
              {tasks.length}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setTasksCollapsed(!tasksCollapsed)}
          className="flex cursor-pointer items-center justify-center rounded-lg p-1.5 text-on-surface-variant transition-colors hover:bg-surface-container-highest hover:text-on-surface"
          aria-label={tasksCollapsed ? "Expand tasks" : "Collapse tasks"}
        >
          {tasksCollapsed ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>
    </div>
  );
}
