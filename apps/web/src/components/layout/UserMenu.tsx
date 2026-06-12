import { useState, useRef, useEffect, useLayoutEffect, useMemo, type RefObject } from "react";
import { createPortal } from "react-dom";
import { Link, useNavigate } from "react-router-dom";
import { Sun, Moon, LogOut } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useThemeMode } from "@providers";
import { useAuth } from "@context";
import { ROUTES, dropdownPanelVariants, modeSpringSoft } from "@lib";

const USER_MENU_WIDTH = 300;
const USER_MENU_ESTIMATED_HEIGHT = 420;

function useUserMenuPosition(open: boolean, anchorRef: RefObject<HTMLButtonElement | null>) {
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  useLayoutEffect(() => {
    if (!open || !anchorRef.current) {
      setPosition(null);
      return;
    }

    const update = () => {
      const rect = anchorRef.current?.getBoundingClientRect();
      if (!rect) return;

      const spaceBelow = window.innerHeight - rect.bottom;
      const openUp = spaceBelow < USER_MENU_ESTIMATED_HEIGHT + 12;
      const top = openUp
        ? Math.max(8, rect.top - USER_MENU_ESTIMATED_HEIGHT - 8)
        : rect.bottom + 8;
      const left = Math.min(
        Math.max(8, rect.right - USER_MENU_WIDTH),
        window.innerWidth - USER_MENU_WIDTH - 8
      );

      setPosition({ top, left });
    };

    update();
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [open, anchorRef]);

  return position;
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

export function UserAvatar({
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

export interface UserMenuProps {
  signOutRedirect?: string;
  showWorkspaceLink?: boolean;
}

export function UserMenu({
  signOutRedirect = ROUTES.login,
  showWorkspaceLink = false,
}: UserMenuProps) {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { mode, toggleTheme } = useThemeMode();
  const [isOpen, setIsOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuPosition = useUserMenuPosition(isOpen, menuButtonRef);

  const name = useMemo(
    () => (user ? displayName(user.full_name, user.email) : "Guest"),
    [user]
  );
  const email = user?.email ?? "";
  const initials = userInitials(name);
  const avatarUrl = user?.avatar_url;

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (menuButtonRef.current?.contains(target)) return;
      if (menuRef.current?.contains(target)) return;
      setIsOpen(false);
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  const handleSignOut = () => {
    logout();
    setIsOpen(false);
    navigate(signOutRedirect, { replace: true });
  };

  const menu = (
    <AnimatePresence initial={false}>
      {isOpen && menuPosition && (
        <motion.div
          ref={menuRef}
          role="menu"
          aria-label="User menu"
          variants={dropdownPanelVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          style={{
            top: menuPosition.top,
            left: menuPosition.left,
            width: USER_MENU_WIDTH,
            transformOrigin: "top right",
          }}
          className="fixed z-[250] glass-gradient-panel border border-outline-variant/40 rounded-[28px] shadow-lg overflow-hidden text-on-surface will-change-[transform,opacity]"
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
                className="w-full px-6 py-2.5 rounded-full bg-surface-container-highest/70 text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface text-xs font-semibold transition-colors duration-200 cursor-pointer outline-none border-0"
              >
                Sign in
              </button>
            </div>
          ) : (
            <div className="px-6 pb-4 flex flex-col gap-2">
              {showWorkspaceLink && (
                <button
                  onClick={() => {
                    setIsOpen(false);
                    navigate(ROUTES.home);
                  }}
                  className="w-full px-4 py-2.5 rounded-full bg-primary text-on-primary text-xs font-semibold hover:opacity-90 transition-opacity cursor-pointer outline-none border-0"
                >
                  Open workspace
                </button>
              )}
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate(ROUTES.account);
                }}
                className="w-full px-4 py-2.5 rounded-full bg-surface-container-highest/70 text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface text-xs font-semibold transition-colors duration-200 cursor-pointer outline-none border-0"
              >
                Account settings
              </button>
              <button
                onClick={handleSignOut}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-full bg-surface-container-highest/70 text-on-surface-variant hover:bg-[#d93025]/10 hover:text-[#d93025] text-xs font-semibold transition-colors duration-200 cursor-pointer outline-none border-0"
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
  );

  return (
    <>
      <div className="relative z-50">
        <button
          ref={menuButtonRef}
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="User menu"
          aria-expanded={isOpen}
          aria-haspopup="menu"
          className="p-0 rounded-full cursor-pointer border-0 outline-none transition-all hover:opacity-90 focus-visible:ring-2 focus-visible:ring-primary/40"
        >
          <UserAvatar
            avatarUrl={isAuthenticated ? avatarUrl : null}
            initials={isAuthenticated ? initials : "?"}
            size="sm"
          />
        </button>
      </div>
      {typeof document !== "undefined" ? createPortal(menu, document.body) : null}
    </>
  );
}
