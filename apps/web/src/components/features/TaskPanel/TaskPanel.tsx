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
  compact = false,
}: {
  text: string;
  active?: boolean;
  depth?: number;
  kind?: TaskPanelItem["kind"];
  status?: TaskPanelItem["status"];
  onClick?: () => void;
  compact?: boolean;
}) {
  const indent = compact ? 0 : Math.min(depth, 5) * INDENT_PX;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex w-full min-w-0 items-center gap-1.5 rounded-lg border text-left transition-all ${
        compact ? "px-2 py-1" : "items-start gap-2 px-2 py-1.5"
      } ${
        active
          ? "border-primary/35 bg-surface-container text-on-surface shadow-sm"
          : "border-outline-variant/25 bg-surface-container-highest/30 text-on-surface-variant hover:border-outline-variant/40 hover:bg-surface-container-highest/60 hover:text-on-surface"
      }`}
      style={compact ? undefined : { paddingLeft: `${8 + indent}px` }}
    >
      {!compact && depth > 0 && (
        <span
          className="pointer-events-none absolute top-0 bottom-3 w-px bg-outline-variant/35"
          style={{ left: `${4 + indent - INDENT_PX / 2}px` }}
          aria-hidden
        />
      )}
      <div
        className={`flex shrink-0 items-center justify-center ${compact ? "h-4 w-4" : "mt-0.5 h-[18px] w-[18px]"}`}
      >
        <StatusIcon active={active} status={status} />
      </div>
      <div className={compact ? "shrink-0" : "mt-0.5 shrink-0"}>
        <KindIcon kind={kind} />
      </div>
      <span
        className={`min-w-0 flex-1 font-medium leading-snug truncate ${
          compact ? "text-xs" : "text-sm break-words"
        }`}
      >
        {text}
      </span>
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
  const usingLiveTasks = liveTasks !== null;
  const tasks = usingLiveTasks ? liveTasks : storedTasks;

  /** Collapsed card: running task, or last task when idle. */
  const collapsedTask = useMemo(() => {
    if (tasks.length === 0) return null;
    const running = tasks.find((t) => t.active || t.status === "active");
    return running ?? tasks[tasks.length - 1];
  }, [tasks]);

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
      className="flex w-full min-w-0 flex-col overflow-hidden rounded-3xl border border-outline-variant/40 glass-gradient-panel shadow-md"
      id="agent-log-panel"
    >
      <div className="flex h-9 shrink-0 items-center justify-between gap-1.5 border-b border-outline-variant/20 bg-surface-container-highest/20 px-2.5">
        <div className="flex min-w-0 flex-1 items-center gap-1.5">
          <Compass size={15} className="shrink-0 text-primary" />
          <span className="truncate text-xs font-semibold text-on-surface">Task manager</span>
          {tasks.length > 0 && (
            <span className="shrink-0 rounded-full bg-surface-container-highest px-1.5 py-0.5 text-[10px] font-medium text-on-surface-variant">
              {tasks.length}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setTasksCollapsed(!tasksCollapsed)}
          className="flex shrink-0 cursor-pointer items-center justify-center rounded-md p-1 text-on-surface-variant transition-colors hover:bg-surface-container-highest hover:text-on-surface"
          aria-label={tasksCollapsed ? "Expand tasks" : "Collapse tasks"}
        >
          {tasksCollapsed ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      <motion.div
        initial={false}
        animate={{ height: tasksCollapsed ? 0 : panelMaxHeight }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="flex min-h-0 flex-col overflow-hidden"
      >
        <AnimatePresence mode="wait">
          {!tasksCollapsed && (
            <motion.div
              key="expanded"
              initial={enterOrSkip(uiReady, { opacity: 0, y: 4 })}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.2 }}
              className="custom-scrollbar flex w-full min-w-0 flex-col gap-1 overflow-y-auto p-2"
              style={{ maxHeight: panelMaxHeight }}
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
                  {agentMode ? "Waiting for agent steps…" : "No tasks yet"}
                </span>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {tasksCollapsed && (
        <div className="shrink-0 border-t border-outline-variant/15 px-2 py-1.5">
          {collapsedTask ? (
            <LogItem
              text={collapsedTask.text}
              active={Boolean(collapsedTask.active || collapsedTask.status === "active")}
              depth={0}
              kind={collapsedTask.kind}
              status={collapsedTask.status}
              compact
              onClick={() => handleTaskClick(collapsedTask.id)}
            />
          ) : (
            <p className="py-1 text-center text-[11px] font-medium text-on-surface-variant/50">
              {agentMode ? "Waiting for agent steps…" : "No tasks yet"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
