import { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, FileText, MessageSquare, Gift, Sun, Moon, ChevronDown, LogOut, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { HeaderIcon } from "../ui";
import { useThemeMode } from "../ThemeProvider";
import { useAuth } from "../../context/AuthContext";
import { ROUTES } from "../../lib/routes";

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (parts[0]?.slice(0, 2) ?? "?").toUpperCase();
}

function displayName(fullName: string | null | undefined, email: string): string {
  if (fullName?.trim()) return fullName.trim();
  return email.split("@")[0] ?? email;
}

export function Header({ sidebarOpen, setSidebarOpen }: HeaderProps) {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { mode, toggleTheme } = useThemeMode();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const name = useMemo(
    () => (user ? displayName(user.full_name, user.email) : "Guest"),
    [user]
  );
  const email = user?.email ?? "";
  const roleLabel = user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : "";
  const initials = userInitials(name);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSignOut = () => {
    logout();
    setIsOpen(false);
    navigate(ROUTES.login, { replace: true });
  };

  return (
    <header className="flex justify-between items-center h-16 px-4 sm:px-8 w-full z-40">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-surface-container-highest rounded-full transition-colors text-on-surface-variant cursor-pointer flex items-center justify-center border-0 outline-none"
        >
          <Menu size={24} />
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-1.5">
          <HeaderIcon title="Documentation" icon={<FileText size={22} />} />
          <HeaderIcon title="Feedback" icon={<MessageSquare size={22} />} />
          <HeaderIcon title="What's new" icon={<Gift size={22} />} />
        </div>

        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 p-1 pr-3 rounded-full bg-surface-container-high/60 hover:bg-surface-container-high border border-outline-variant/20 hover:border-outline-variant/40 transition-all cursor-pointer text-on-surface shadow-sm focus:outline-none"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden border border-outline-variant/30 flex-shrink-0 bg-primary/15 flex items-center justify-center">
              {isAuthenticated ? (
                <span className="text-[11px] font-bold text-primary">{initials}</span>
              ) : (
                <span className="text-[11px] font-bold text-on-surface-variant">?</span>
              )}
            </div>
            <div className="hidden sm:flex flex-col items-start text-left ml-1.5">
              <span className="text-xs font-semibold leading-tight text-on-surface">{name}</span>
              <span className="text-[10px] text-on-surface-variant leading-none">
                {isAuthenticated ? roleLabel : "Not signed in"}
              </span>
            </div>
            <ChevronDown
              size={14}
              className={`text-on-surface-variant ml-1.5 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
            />
          </button>

          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="absolute right-0 mt-3 w-[280px] sm:w-[320px] bg-surface-container-highest border border-outline-variant/40 rounded-[28px] shadow-2xl z-50 overflow-hidden p-0 text-on-surface"
              >
                <div className="flex items-center justify-between px-6 pt-5 pb-3">
                  <span className="text-[11px] font-medium text-on-surface-variant/70 tracking-wide uppercase select-none truncate max-w-[200px]">
                    {isAuthenticated ? email : "Sign in to continue"}
                  </span>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 hover:bg-surface-container-high rounded-full transition-colors cursor-pointer text-on-surface-variant flex items-center justify-center border-0 outline-none"
                  >
                    <X size={16} />
                  </button>
                </div>

                <div className="flex flex-col items-center text-center px-6 pb-6 pt-2">
                  <div className="w-20 h-20 rounded-full overflow-hidden border border-outline-variant/30 shadow-md mb-3.5 flex-shrink-0 bg-primary/15 flex items-center justify-center">
                    <span className="text-2xl font-semibold text-primary">{isAuthenticated ? initials : "?"}</span>
                  </div>

                  <span className="text-xl font-medium text-on-surface select-none">
                    {isAuthenticated ? `Hi, ${name.split(" ")[0]}!` : "Welcome"}
                  </span>
                  <span className="text-xs text-on-surface-variant/80 mt-0.5 mb-5 select-none">{name}</span>

                  {!isAuthenticated ? (
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        navigate(ROUTES.login);
                      }}
                      className="px-6 py-2.5 rounded-full bg-gradient-to-b from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 text-xs font-semibold transition-all duration-200 cursor-pointer outline-none shadow-sm border-none"
                    >
                      Sign in
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate(ROUTES.settings)}
                      className="px-6 py-2.5 rounded-full border border-outline-variant/40 hover:bg-primary/5 text-xs font-semibold text-primary transition-all duration-200 cursor-pointer outline-none shadow-sm"
                    >
                      Account settings
                    </button>
                  )}
                </div>

                <div className="bg-surface-container-high/40 border-t border-outline-variant/20 px-6 py-3 flex flex-col gap-1">
                  <div
                    onClick={toggleTheme}
                    className="flex items-center justify-between p-2 hover:bg-surface-container-high rounded-xl transition-colors cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-3 text-on-surface">
                      {mode === "dark" ? (
                        <Moon size={16} className="text-primary" />
                      ) : (
                        <Sun size={16} className="text-primary" />
                      )}
                      <span className="text-xs font-semibold">Dark Theme</span>
                    </div>
                    <div
                      className={`w-9 h-5 rounded-full p-0.5 flex items-center border transition-colors ${
                        mode === "dark"
                          ? "bg-primary/20 border-primary/40 justify-end"
                          : "bg-surface-container border-outline-variant/40 justify-start"
                      }`}
                    >
                      <motion.div
                        layout
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className={`w-3.5 h-3.5 rounded-full flex items-center justify-center shadow-sm ${
                          mode === "dark" ? "bg-primary" : "bg-outline-variant"
                        }`}
                      />
                    </div>
                  </div>
                </div>

                {isAuthenticated && (
                  <div className="border-t border-outline-variant/20 px-6 py-4 flex justify-center bg-surface-container-high/20">
                    <button
                      onClick={handleSignOut}
                      className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-full border border-outline-variant/40 hover:bg-error-container/15 hover:text-error hover:border-error/40 text-xs font-semibold text-on-surface-variant transition-all duration-200 cursor-pointer outline-none bg-surface-container-highest shadow-sm"
                    >
                      <LogOut size={14} />
                      <span>Sign out</span>
                    </button>
                  </div>
                )}

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
