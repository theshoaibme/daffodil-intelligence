import { useState, useRef, useEffect } from "react";
import { Menu, FileText, MessageSquare, Gift, Sun, Moon, ChevronDown, LogOut } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { HeaderIcon } from "../ui";
import { useThemeMode } from "../ThemeProvider";

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export function Header({ sidebarOpen, setSidebarOpen }: HeaderProps) {
  const { mode, toggleTheme } = useThemeMode();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="flex justify-between items-center h-16 px-8 w-full z-20">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-surface-container-highest rounded-full transition-colors text-on-surface-variant cursor-pointer flex items-center justify-center border-0 outline-none"
        >
          <Menu size={24} />
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <HeaderIcon title="Documentation" icon={<FileText size={22} />} />
          <HeaderIcon title="Feedback" icon={<MessageSquare size={22} />} />
          <HeaderIcon title="What's new" icon={<Gift size={22} />} />
        </div>

        {/* User Avatar Button & Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 p-1 pr-3 rounded-full bg-surface-container-high/60 hover:bg-surface-container-high border border-outline-variant/20 hover:border-outline-variant/40 transition-all cursor-pointer text-on-surface shadow-sm focus:outline-none"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden border border-outline-variant/30 flex-shrink-0">
              <img 
                alt="User profile" 
                className="w-full h-full object-cover" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ" 
              />
            </div>
            <div className="hidden sm:flex flex-col items-start text-left ml-1.5">
              <span className="text-xs font-semibold leading-tight text-on-surface">Alex Carter</span>
              <span className="text-[10px] text-on-surface-variant leading-none">Developer</span>
            </div>
            <ChevronDown size={14} className={`text-on-surface-variant ml-1.5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="absolute right-0 mt-2 w-64 bg-surface-container-highest/95 backdrop-blur-xl border border-outline-variant/40 rounded-2xl shadow-xl z-50 overflow-hidden p-3"
              >
                {/* User Profile Card */}
                <div className="flex items-center gap-3 p-2 pb-3 border-b border-outline-variant/20">
                  <div className="w-10 h-10 rounded-full overflow-hidden border border-outline-variant/30 flex-shrink-0">
                    <img 
                      alt="User Avatar"
                      className="w-full h-full object-cover" 
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ" 
                    />
                  </div>
                  <div className="flex flex-col text-left">
                    <span className="text-sm font-bold text-on-surface leading-tight">Alex Carter</span>
                    <span className="text-[11px] text-on-surface-variant truncate w-[160px]">alex.carter@gmail.com</span>
                  </div>
                </div>

                {/* Theme Settings Mode */}
                <div className="flex items-center justify-between p-2.5 my-1.5 hover:bg-surface-container/30 rounded-lg transition-colors">
                  <div className="flex items-center gap-2.5 text-on-surface">
                    {mode === 'dark' ? <Moon size={16} className="text-primary" /> : <Sun size={16} className="text-primary" />}
                    <span className="text-sm font-medium">Dark Theme</span>
                  </div>
                  {/* Google Switch */}
                  <div 
                    onClick={toggleTheme}
                    className={`w-11 h-6 rounded-full p-0.5 flex items-center cursor-pointer border transition-colors ${
                      mode === 'dark' 
                        ? 'bg-primary/20 border-primary/40 justify-end' 
                        : 'bg-surface-container border-outline-variant/40 justify-start'
                    }`}
                  >
                    <motion.div
                      layout
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      className={`w-[18px] h-[18px] rounded-full flex items-center justify-center shadow-sm ${
                        mode === 'dark' ? 'bg-primary text-white' : 'bg-outline text-white'
                      }`}
                    >
                      {mode === 'dark' ? <Moon size={8} /> : <Sun size={8} />}
                    </motion.div>
                  </div>
                </div>

                {/* Divider */}
                <div className="h-[1px] bg-outline-variant/20 my-1" />

                {/* Logout Option */}
                <button
                  onClick={() => {
                    alert("Logging out...");
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 p-2.5 hover:bg-error-container/20 rounded-lg transition-colors text-error text-left cursor-pointer font-medium mt-1 border-0 outline-none"
                >
                  <LogOut size={16} />
                  <span className="text-sm">Log out</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
