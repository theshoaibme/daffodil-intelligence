import { useRef, useEffect } from "react";
import { Infinity, ChevronDown, Compass, Monitor, Brain, Settings2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { DropdownItem } from "../../ui";

interface AgentSelectorProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  selectedTools: string[];
  onToggleTool: (toolName: string) => void;
  onCopycatMode?: () => void;
  copycatActive?: boolean;
  mcpConfigured?: boolean;
  onConfigureMcp?: () => void;
}

export function AgentSelector({
  isOpen,
  setIsOpen,
  selectedTools,
  onToggleTool,
  onCopycatMode,
  copycatActive = false,
  mcpConfigured = true,
  onConfigureMcp,
}: AgentSelectorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mcpSelected = selectedTools.includes("MCP");

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setIsOpen]);

  const tools = [
    { text: "MCP", icon: <Compass size={16} strokeWidth={1.75} />, isMcp: true },
    { text: "Agent", icon: <Monitor size={16} strokeWidth={1.75} /> },
    { text: "Research", icon: <Compass size={16} strokeWidth={1.75} /> },
    { text: "Planning", icon: <Brain size={16} strokeWidth={1.75} /> },
  ];

  const modes = [{ text: "Copycat", icon: <Monitor size={16} strokeWidth={1.75} /> }];

  const handleMcpClick = () => {
    if (!mcpConfigured) {
      setIsOpen(false);
      onConfigureMcp?.();
      return;
    }
    onToggleTool("MCP");
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Agent options"
        aria-expanded={isOpen}
        className="flex items-center gap-1 bg-surface-container-highest hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors rounded-full cursor-pointer outline-none border-0 pl-2 pr-1.5 py-1"
      >
        <Infinity size={14} strokeWidth={2} />
        <span className="text-xs font-medium">Agent</span>
        <ChevronDown size={12} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className="absolute bottom-full left-0 mb-2 w-56 glass-gradient-panel border border-outline-variant/40 rounded-2xl shadow-md z-[60] overflow-hidden flex flex-col py-1"
          >
            <div className="px-1 py-1">
              {tools.map((item) =>
                item.isMcp ? (
                  <div key={item.text} className="relative flex items-center pr-1">
                    <div className="flex-1 min-w-0">
                      <DropdownItem
                        icon={item.icon}
                        text={item.text}
                        active={mcpSelected && mcpConfigured}
                        onClick={handleMcpClick}
                      />
                    </div>
                    {mcpConfigured && (
                      <button
                        type="button"
                        aria-label="Manage MCP servers"
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsOpen(false);
                          onConfigureMcp?.();
                        }}
                        className={`absolute top-1/2 -translate-y-1/2 p-1 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high border-0 cursor-pointer ${
                          mcpSelected ? "right-9" : "right-2"
                        }`}
                      >
                        <Settings2 size={14} />
                      </button>
                    )}
                  </div>
                ) : (
                  <DropdownItem
                    key={item.text}
                    icon={item.icon}
                    text={item.text}
                    active={selectedTools.includes(item.text)}
                    onClick={() => onToggleTool(item.text)}
                  />
                )
              )}
            </div>

            <div className="mx-2.5 my-1 border-t border-outline-variant/30" />

            <div className="px-1 py-1">
              {modes.map((mode) => (
                <DropdownItem
                  key={mode.text}
                  icon={mode.icon}
                  text={mode.text}
                  active={copycatActive}
                  onClick={() => {
                    setIsOpen(false);
                    onCopycatMode?.();
                  }}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
