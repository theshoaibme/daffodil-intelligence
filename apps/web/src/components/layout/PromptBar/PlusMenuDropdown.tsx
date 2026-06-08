import { useRef, useEffect } from "react";
import { Plus, Compass, Monitor, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { DropdownItem } from "../../ui";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../../lib/routes";

interface PlusMenuDropdownProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  selectedTools: string[];
  onToggleTool: (toolName: string) => void;
}

export function PlusMenuDropdown({ isOpen, setIsOpen, selectedTools, onToggleTool }: PlusMenuDropdownProps) {
  const plusMenuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close plus menu on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (plusMenuRef.current && !plusMenuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setIsOpen]);

  const tools = [
    { text: "MCP", icon: <Compass className="text-primary" size={20} /> },
    { text: "Agent", icon: <Monitor className="text-primary" size={20} /> },
    { text: "Research", icon: <Compass className="text-primary" size={20} /> },
    { text: "Task", icon: <CheckCircle2 className="text-primary" size={20} /> },
  ];

  const modes = [
    { text: "Copycat Mode", icon: <Monitor className="text-tertiary" size={20} />, path: ROUTES.computer },
  ];

  return (
    <div className="relative" ref={plusMenuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest rounded-full transition-all cursor-pointer border-0 outline-none"
      >
        <Plus size={22} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className="absolute bottom-full left-0 mb-3 w-56 bg-surface-container-high border border-outline-variant/40 rounded-2xl shadow-xl z-[60] overflow-hidden flex flex-col"
          >
            <div className="p-2 space-y-1">
              <div className="px-2 pb-1 text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">Tools</div>
              {tools.map((item) => (
                <DropdownItem 
                  key={item.text} 
                  icon={item.icon} 
                  text={item.text} 
                  active={selectedTools.includes(item.text)}
                  onClick={() => onToggleTool(item.text)}
                />
              ))}
            </div>
            
            <div className="border-t border-outline-variant/20 p-2 space-y-1">
              <div className="px-2 pb-1 text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">Modes</div>
              {modes.map((mode) => (
                <DropdownItem 
                  key={mode.text} 
                  icon={mode.icon} 
                  text={mode.text} 
                  active={false}
                  onClick={() => {
                    setIsOpen(false);
                    navigate(mode.path);
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
