import { useState, useRef, useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FileText, MessageSquare, Gift, Sun, Moon, LogOut } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { HeaderIcon } from "../ui";
import { useThemeMode } from "../ThemeProvider";
import { useAuth } from "../../context/AuthContext";
import { ROUTES } from "../../lib/routes";
import { dropdownPanelVariants, modeSpringSoft, sidebarWidthTransition } from "../../lib/motion";
import {
  SIDEBAR_WIDTH_COLLAPSED,
  SIDEBAR_WIDTH_EXPANDED,
} from "./Sidebar/Sidebar";

function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (parts[0]?.slice(0, 2) ?? "?").toUpperCase();
}

function displayName(fullName: string | null | undefined, email: string): string {
  if (fullName?.trim()) return fullName.trim();
  return email.split("@")[0] ?? email;
}

function UserAvatar({
  avatarUrl,
  initials,
  size = "sm",
}: {
  avatarUrl?: string | null;
  initials: string;
  size?: "sm" | "lg";
}) {
  const [failed, setFailed] = useState(false);
  const sizeClass = size === "lg" ? "w-20 h-20 mb-3.5" : "w-8 h-8";
  const textClass = size === "lg" ? "text-2xl" : "text-[11px]";

  if (avatarUrl && !failed) {
    return (
      <img
        src={avatarUrl}
        alt=""
        referrerPolicy="no-referrer"
        className={`${sizeClass} rounded-full object-cover flex-shrink-0`}
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <div
      className={`${sizeClass} rounded-full overflow-hidden flex-shrink-0 bg-primary/15 flex items-center justify-center`}
    >
      <span className={`${textClass} font-bold text-primary`}>{initials}</span>
    </div>
  );
}

export interface HeaderProps {
  sidebarOpen?: boolean;
}

export function Header({ sidebarOpen = false }: HeaderProps) {
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
  const initials = userInitials(name);
  const avatarUrl = user?.avatar_url;

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
    <header className="sticky top-0 z-30 shrink-0 flex justify-between items-center h-16 pr-4 sm:pr-6 w-full bg-background/90 backdrop-blur-md">
      <motion.div
        className="flex items-center gap-2.5 min-w-0"
        initial={false}
        animate={{
          paddingLeft: (sidebarOpen ? SIDEBAR_WIDTH_EXPANDED : SIDEBAR_WIDTH_COLLAPSED) + 16,
        }}
        transition={sidebarWidthTransition}
      >
        <Link
          to={ROUTES.home}
          className="flex items-center gap-2.5 min-w-0 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
        >
          <span className="text-xl sm:text-2xl font-bold tracking-tight truncate leading-none">
            <span className="bg-gradient-to-b from-blue-500 to-blue-600 bg-clip-text text-transparent">
              Daffodil
            </span>
            <span className="text-on-surface"> Intelligence</span>
          </span>
        </Link>
      </motion.div>

      <div className="flex items-center gap-2 sm:gap-4 shrink-0">
        <div className="hidden sm:flex items-center gap-1.5">
          <HeaderIcon title="Documentation" icon={<FileText size={22} />} />
          <HeaderIcon title="Feedback" icon={<MessageSquare size={22} />} />
          <HeaderIcon title="What's new" icon={<Gift size={22} />} />
        </div>

        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="User menu"
            aria-expanded={isOpen}
            className="p-0 rounded-full cursor-pointer border-0 outline-none transition-all hover:opacity-90 focus-visible:ring-2 focus-visible:ring-primary/40"
          >
            <UserAvatar
              avatarUrl={isAuthenticated ? avatarUrl : null}
              initials={isAuthenticated ? initials : "?"}
              size="sm"
            />
          </button>

          <AnimatePresence initial={false}>
            {isOpen && (
              <motion.div
                key="user-menu"
                variants={dropdownPanelVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                style={{ transformOrigin: "top right" }}
                className="absolute right-0 top-full mt-2 w-[280px] sm:w-[300px] glass-gradient-panel border border-outline-variant/40 rounded-[28px] shadow-md z-50 overflow-hidden text-on-surface will-change-[transform,opacity]"
              >
                <div className="flex flex-col items-center text-center px-6 pt-6 pb-5">
                  <UserAvatar avatarUrl={avatarUrl} initials={initials} size="lg" />

                  <span
                    className="text-lg font-medium text-on-surface select-none mt-4 max-w-full truncate px-2"
                    title={isAuthenticated ? name : undefined}
                  >
                    {isAuthenticated ? name : "Welcome"}
                  </span>

                  {isAuthenticated && email && (
                    <span className="text-xs text-on-surface-variant/80 mt-1 select-none normal-case">
                      {email}
                    </span>
                  )}

                  {!isAuthenticated && (
                    <span className="text-xs text-on-surface-variant/80 mt-1 select-none">
                      Sign in to continue
                    </span>
                  )}
                </div>

                {!isAuthenticated ? (
                  <div className="px-6 pb-5 flex justify-center">
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        navigate(ROUTES.login);
                      }}
                      className="w-full px-6 py-2.5 rounded-full bg-gradient-to-b from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 text-xs font-semibold transition-all duration-200 cursor-pointer outline-none shadow-sm border-0"
                    >
                      Sign in
                    </button>
                  </div>
                ) : (
                  <div className="px-6 pb-4 flex flex-col gap-2">
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        navigate(ROUTES.account);
                      }}
                      className="w-full px-4 py-2.5 rounded-full bg-primary text-on-primary hover:opacity-90 text-xs font-semibold transition-opacity duration-200 cursor-pointer outline-none border-0"
                    >
                      Account settings
                    </button>
                    <button
                      onClick={handleSignOut}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-full bg-[#d93025] text-white hover:bg-[#c5221f] text-xs font-semibold transition-colors duration-200 cursor-pointer outline-none border-0"
                    >
                      <LogOut size={14} />
                      <span>Sign out</span>
                    </button>
                  </div>
                )}

                <div className="px-4 pb-3">
                  <div
                    onClick={toggleTheme}
                    className="flex items-center justify-between p-2.5 bg-surface-container-highest/70 hover:bg-surface-container-highest rounded-xl transition-colors cursor-pointer select-none"
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
                      className={`w-9 h-5 rounded-full p-0.5 flex items-center transition-colors ${
                        mode === "dark"
                          ? "bg-primary justify-end"
                          : "bg-surface-container justify-start"
                      }`}
                    >
                      <motion.div
                        layout
                        transition={modeSpringSoft}
                        className={`w-3.5 h-3.5 rounded-full shadow-sm ${
                          mode === "dark" ? "bg-on-primary" : "bg-outline-variant"
                        }`}
                      />
                    </div>
                  </div>
                </div>

                <div className="py-3 flex items-center justify-center gap-3 text-[10px] text-on-surface-variant/50 select-none">
                  <Link to={ROUTES.privacy} className="hover:underline" onClick={() => setIsOpen(false)}>
                    Privacy Policy
                  </Link>
                  <span>•</span>
                  <Link to={ROUTES.terms} className="hover:underline" onClick={() => setIsOpen(false)}>
                    Terms of Service
                  </Link>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
