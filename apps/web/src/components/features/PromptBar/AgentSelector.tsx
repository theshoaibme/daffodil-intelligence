import { useRef, useEffect } from "react";
import { ChevronDown, Settings2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { AgentMode } from "@lib";
import { AGENT_MODE_ICONS, COPYCAT_MODE_ICON } from "./agentModeIcons";
import { DropdownItem } from "../../ui";

interface AgentSelectorProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  selectedMode: AgentMode;
  onSelectMode: (mode: AgentMode) => void;
  onCopycatMode?: () => void;
  copycatActive?: boolean;
  mcpConfigured?: boolean;
  onConfigureMcp?: () => void;
}

export function AgentSelector({
  isOpen,
  setIsOpen,
  selectedMode,
  onSelectMode,
  onCopycatMode,
  copycatActive = false,
  mcpConfigured = true,
  onConfigureMcp,
}: AgentSelectorProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setIsOpen]);

  const tools: AgentMode[] = ["MCP", "Agent", "Research", "Planning"];

  const selectMode = (mode: AgentMode) => {
    onSelectMode(mode);
    setIsOpen(false);
  };

  const handleMcpClick = () => {
    if (!mcpConfigured) {
      setIsOpen(false);
      onConfigureMcp?.();
      return;
    }
    selectMode("MCP");
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
        <span className="shrink-0 [&>svg]:size-3.5">{AGENT_MODE_ICONS[selectedMode]}</span>
        <span className="text-xs font-medium leading-none">{selectedMode}</span>
        <ChevronDown size={13} className={`shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className="absolute bottom-full left-0 mb-2 w-52 glass-gradient-panel border border-outline-variant/40 rounded-2xl shadow-md z-[60] overflow-hidden flex flex-col py-1"
          >
            <div className="px-1 py-1">
              {tools.map((mode) =>
                mode === "MCP" ? (
                  <div key={mode} className="relative flex items-center pr-1">
                    <div className="flex-1 min-w-0">
                      <DropdownItem
                        icon={AGENT_MODE_ICONS.MCP}
                        text={mode}
                        active={selectedMode === "MCP" && mcpConfigured}
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
                          selectedMode === "MCP" ? "right-9" : "right-2"
                        }`}
                      >
                        <Settings2 size={13} />
                      </button>
                    )}
                  </div>
                ) : (
                  <DropdownItem
                    key={mode}
                    icon={AGENT_MODE_ICONS[mode]}
                    text={mode}
                    active={selectedMode === mode}
                    onClick={() => selectMode(mode)}
                  />
                )
              )}
            </div>

            <div className="mx-2.5 my-1 border-t border-outline-variant/30" />

            <div className="px-1 py-1">
              <DropdownItem
                icon={COPYCAT_MODE_ICON}
                text="Copycat"
                active={copycatActive}
                onClick={() => {
                  setIsOpen(false);
                  onCopycatMode?.();
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
