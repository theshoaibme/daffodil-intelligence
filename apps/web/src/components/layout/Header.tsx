import { useState, useRef, useEffect } from "react";
import { Menu, FileText, MessageSquare, Gift, Sun, Moon, ChevronDown, LogOut, X, Camera } from "lucide-react";
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
    <header className="flex justify-between items-center h-16 px-8 w-full z-40">
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
                className="absolute right-0 mt-3 w-[320px] bg-surface-container-highest border border-outline-variant/40 rounded-[28px] shadow-2xl z-50 overflow-hidden p-0 text-on-surface"
              >
                {/* Top Info Bar & Close Button */}
                <div className="flex items-center justify-between px-6 pt-5 pb-3">
                  <span className="text-[11px] font-medium text-on-surface-variant/70 tracking-wide uppercase select-none">
                    alex.carter@gmail.com
                  </span>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 hover:bg-surface-container-high rounded-full transition-colors cursor-pointer text-on-surface-variant flex items-center justify-center border-0 outline-none"
                  >
                    <X size={16} />
                  </button>
                </div>

                {/* Main Account Identity Block */}
                <div className="flex flex-col items-center text-center px-6 pb-6 pt-2">
                  {/* Huge Circle Avatar Wrapper with Camera Hover effect */}
                  <div className="relative group w-20 h-20 rounded-full overflow-hidden border border-outline-variant/30 shadow-md mb-3.5 flex-shrink-0 cursor-pointer">
                    <img 
                      alt="User Avatar"
                      className="w-full h-full object-cover" 
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ" 
                    />
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <Camera size={18} className="text-white" />
                    </div>
                  </div>

                  <span className="text-xl font-medium text-on-surface select-none">
                    Hi, Alex!
                  </span>
                  <span className="text-xs text-on-surface-variant/80 mt-0.5 mb-5 select-none">
                    Alex Carter
                  </span>

                  {/* Google Manage Account Capsule */}
                  <button
                    onClick={() => alert("Managing account settings...")}
                    className="px-6 py-2.5 rounded-full border border-outline-variant/40 hover:bg-primary/5 text-xs font-semibold text-primary transition-all duration-200 cursor-pointer outline-none shadow-sm"
                  >
                    Manage your Daffodil Account
                  </button>
                </div>

                {/* Extra Options Block */}
                <div className="bg-surface-container-high/40 border-t border-outline-variant/20 px-6 py-3 flex flex-col gap-1">
                  {/* Theme Switcher Toggle Option */}
                  <div 
                    onClick={toggleTheme}
                    className="flex items-center justify-between p-2 hover:bg-surface-container-high rounded-xl transition-colors cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-3 text-on-surface">
                      {mode === 'dark' ? <Moon size={16} className="text-primary" /> : <Sun size={16} className="text-primary" />}
                      <span className="text-xs font-semibold">Dark Theme</span>
                    </div>
                    {/* Authentic Switch */}
                    <div 
                      className={`w-9 h-5 rounded-full p-0.5 flex items-center border transition-colors ${
                        mode === 'dark' 
                          ? 'bg-primary/20 border-primary/40 justify-end' 
                          : 'bg-surface-container border-outline-variant/40 justify-start'
                      }`}
                    >
                      <motion.div
                        layout
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className={`w-3.5 h-3.5 rounded-full flex items-center justify-center shadow-sm ${
                          mode === 'dark' ? 'bg-primary' : 'bg-outline-variant'
                        }`}
                      />
                    </div>
                  </div>
                </div>

                {/* Logout Capsule Switcher Bar */}
                <div className="border-t border-outline-variant/20 px-6 py-4 flex justify-center bg-surface-container-high/20">
                  <button
                    onClick={() => {
                      alert("Signing out...");
                      setIsOpen(false);
                    }}
                    className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-full border border-outline-variant/40 hover:bg-error-container/15 hover:text-error hover:border-error/40 text-xs font-semibold text-on-surface-variant transition-all duration-200 cursor-pointer outline-none bg-surface-container-highest shadow-sm"
                  >
                    <LogOut size={14} />
                    <span>Sign out of all accounts</span>
                  </button>
                </div>

                {/* Google-Style Footer */}
                <div className="border-t border-outline-variant/10 py-3 flex items-center justify-center gap-3 text-[10px] text-on-surface-variant/40 select-none">
                  <span className="hover:underline cursor-pointer">Privacy Policy</span>
                  <span>•</span>
                  <span className="hover:underline cursor-pointer">Terms of Service</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
