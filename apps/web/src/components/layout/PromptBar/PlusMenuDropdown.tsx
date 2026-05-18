import { useRef, useEffect } from "react";
import { Plus, Compass, Monitor, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { DropdownItem } from "../../ui";

interface PlusMenuDropdownProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export function PlusMenuDropdown({ isOpen, setIsOpen }: PlusMenuDropdownProps) {
  const plusMenuRef = useRef<HTMLDivElement>(null);

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
            className="absolute bottom-full left-0 mb-3 w-56 bg-surface-container-high border border-outline-variant/40 rounded-2xl shadow-xl z-[60] overflow-hidden"
          >
            <div className="p-2 space-y-1">
              <DropdownItem icon={<Compass className="text-primary" size={20} />} text="MCP" />
              <DropdownItem icon={<Monitor className="text-primary" size={20} />} text="Agent" />
              <DropdownItem icon={<Compass className="text-primary" size={20} />} text="Research" />
              <DropdownItem icon={<CheckCircle2 className="text-primary" size={20} />} text="Task" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
