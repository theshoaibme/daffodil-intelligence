import { useEffect } from "react";
import { Compass, ChevronUp, ChevronDown, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader } from "../../ui/Loader";
import { useLocalStorageState } from "@hooks";
import { enterOrSkip } from "@lib";

export interface TaskItem {
  id: string;
  text: string;
  active?: boolean;
  depth?: number;
  parallelGroup?: string;
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

export function LogItem({
  text,
  active = false,
  depth = 0,
  onClick,
}: {
  text: string;
  active?: boolean;
  depth?: number;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-2 p-2 rounded-lg border text-left cursor-pointer transition-all ${active
          ? 'bg-surface-container border-primary/35 text-on-surface shadow-sm'
          : 'bg-surface-container-highest/30 border-outline-variant/25 hover:bg-surface-container-highest/60 hover:border-outline-variant/40 text-on-surface-variant hover:text-on-surface'
        }`}
      style={{ marginLeft: depth > 0 ? `${Math.min(depth, 4) * 12}px` : undefined }}
    >
      <div className="flex-shrink-0 w-[18px] h-[18px] flex items-center justify-center">
        {active ? (
          <Loader diameter={16} strokeWidth={2} color="primary" />
        ) : (
          <CheckCircle2 size={18} className="text-primary" />
        )}
      </div>
      <span className="text-sm font-medium flex-1 truncate pr-1">{text}</span>
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
  const activeTask = tasks.find(t => t.active);

  const handleTaskClick = (taskId: string) => {
    if (usingLiveTasks) return;
    setStoredTasks(prev => prev.map(t => ({
      ...t,
      active: t.id === taskId
    })));
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
      className="w-full glass-gradient-panel border border-outline-variant/40 shadow-md flex flex-col overflow-hidden rounded-3xl" 
      id="agent-log-panel"
    >
      {/* Smooth Spring Panel Body */}
      <motion.div
        initial={false}
        animate={{ height: tasksCollapsed ? 56 : "auto" }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="overflow-hidden flex flex-col justify-end max-h-[min(200px,28dvh)]"
      >
        <AnimatePresence mode="wait">
          {tasksCollapsed ? (
            <motion.div
              key="collapsed"
              initial={enterOrSkip(uiReady, { opacity: 0, y: -5 })}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.2 }}
              className="p-3 border-b border-outline-variant/20 h-[56px] flex items-center justify-center"
            >
              {activeTask ? (
                <LogItem 
                  text={activeTask.text} 
                  active 
                  onClick={() => handleTaskClick(activeTask.id)} 
                />
              ) : (
                <span className="text-xs font-medium text-on-surface-variant/50">
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
              className="flex-1 p-3 custom-scrollbar overflow-y-auto max-h-[min(196px,26dvh)] min-h-[120px] space-y-1.5 flex flex-col items-center justify-center"
            >
              {tasks.length > 0 ? (
                tasks.map(task => (
                  <LogItem 
                    key={task.id} 
                    text={task.text} 
                    active={task.active}
                    depth={task.depth}
                    onClick={() => handleTaskClick(task.id)}
                  />
                ))
              ) : (
                <span className="text-xs font-medium text-on-surface-variant/50">
                  {agentMode ? "Waiting for agents…" : "No tasks active"}
                </span>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* Panel Header */}
      <div className="flex items-center justify-between border-t border-outline-variant/20 bg-surface-container-highest/20 p-2.5 px-3">
        <div className="flex items-center gap-2">
          <Compass size={18} className="text-primary" />
          <span className="text-sm font-semibold text-on-surface">
            {agentMode ? "Agent tasks" : "Task"}
          </span>
        </div>
        <button 
          onClick={() => setTasksCollapsed(!tasksCollapsed)}
          className="p-1.5 hover:bg-surface-container-highest hover:text-on-surface rounded-lg transition-colors text-on-surface-variant cursor-pointer flex items-center justify-center"
        >
          {tasksCollapsed ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>
    </div>
  );
}
