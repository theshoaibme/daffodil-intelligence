import { useState } from "react";
import { Compass, ChevronUp, ChevronDown, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader } from "../../ui/Loader";

export interface TaskItem {
  id: string;
  text: string;
  active?: boolean;
}

export interface TaskPanelProps {
  tasksCollapsed: boolean;
  setTasksCollapsed: (collapsed: boolean) => void;
}

export const initialTasks: TaskItem[] = [
  { id: "1", text: "also right side panel create div in react", active: true },
  { id: "2", text: "Refine the sidebar collapse animation" },
  { id: "3", text: "Implement a sticky sidebar layout border" },
  { id: "4", text: "Make the chat input dynamically grow" },
  { id: "5", text: "Make the chat input dynamic and rounded" }
];

export function LogItem({
  text,
  active = false,
  onClick
}: {
  text: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-2 p-2 rounded-lg border text-left cursor-pointer transition-all ${active
          ? 'bg-surface-container border-primary/35 text-on-surface shadow-sm'
          : 'bg-surface-container-highest/30 border-outline-variant/25 hover:bg-surface-container-highest/60 hover:border-outline-variant/40 text-on-surface-variant hover:text-on-surface'
        }`}
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

export function TaskPanel({
  tasksCollapsed,
  setTasksCollapsed
}: TaskPanelProps) {
  const [tasks, setTasks] = useState<TaskItem[]>(initialTasks);
  const activeTask = tasks.find(t => t.active);

  const handleTaskClick = (taskId: string) => {
    setTasks(prev => prev.map(t => ({
      ...t,
      active: t.id === taskId
    })));
  };

  return (
    <div 
      className="w-full glass-gradient-panel border border-outline-variant/40 shadow-md flex flex-col overflow-hidden rounded-3xl" 
      id="agent-log-panel"
    >
      {/* Smooth Spring Panel Body */}
      <motion.div
        animate={{ height: tasksCollapsed ? 56 : 200 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="overflow-hidden flex flex-col justify-end"
      >
        <AnimatePresence initial={false} mode="wait">
          {tasksCollapsed ? (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.15 }}
              className="p-3 border-b border-outline-variant/20 h-[56px] flex items-center"
            >
              {activeTask && (
                <LogItem 
                  text={activeTask.text} 
                  active 
                  onClick={() => handleTaskClick(activeTask.id)} 
                />
              )}
            </motion.div>
          ) : (
            <motion.div
              key="expanded"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              transition={{ duration: 0.15 }}
              className="flex-1 p-3 custom-scrollbar overflow-y-auto max-h-[196px] space-y-1.5 h-[196px]"
            >
              {tasks.map(task => (
                <LogItem 
                  key={task.id} 
                  text={task.text} 
                  active={task.active} 
                  onClick={() => handleTaskClick(task.id)}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* Panel Header */}
      <div className="flex items-center justify-between border-t border-outline-variant/20 bg-surface-container-highest/20 p-2.5 px-3">
        <div className="flex items-center gap-2">
          <Compass size={18} className="text-primary" />
          <span className="text-sm font-semibold text-on-surface">Task</span>
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
