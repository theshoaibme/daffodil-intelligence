import { useMemo, useState, useEffect, type ReactNode } from "react";
import { Menu, Search, Settings, Plus, LayoutGrid, Sparkles, type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { useLocation, useNavigate } from "react-router-dom";
import { ROUTES } from "../../../lib/routes";
import type { SidebarProps } from "./types";
import { enterOrSkip, sidebarPanelTransition, sidebarWidthTransition } from "../../../lib/motion";
import { useChatHistory } from "../../../context/ChatHistoryContext";
import { ChatHistoryItem } from "./ChatHistoryItem";
 
export type { SidebarProps } from "./types";
export const SIDEBAR_WIDTH_EXPANDED = 280;
export const SIDEBAR_WIDTH_COLLAPSED = 56;
 
const iconBtn =
  "shrink-0 p-2 rounded-full transition-colors cursor-pointer flex items-center justify-center border-0 outline-none focus-visible:ring-2 focus-visible:ring-primary/40";
 
const SIDEBAR_NAV = [
  { to: ROUTES.agentHub, label: "Agents", icon: LayoutGrid },
  { to: ROUTES.skills, label: "Skills", icon: Sparkles },
] as const;
 
function matchesSearch(item: { title: string }, query: string) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  return item.title.toLowerCase().includes(normalized);
}
 
function SidebarNavLink({
  label,
  icon: Icon,
  active,
  onClick,
}: {
  label: string;
  icon: LucideIcon;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all border-0 cursor-pointer text-left ${
        active
          ? "bg-primary text-on-primary"
          : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
      }`}
    >
      <Icon size={18} />
      {label}
    </button>
  );
}
 
function RailButton({
  label,
  onClick,
  active = false,
  children,
}: {
  label: string;
  onClick: () => void;
  active?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className={`${iconBtn} ${
        active
          ? "bg-primary/10 text-primary"
          : "text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface"
      }`}
    >
      {children}
    </button>
  );
}
 
export function Sidebar({
  sidebarOpen,
  setSidebarOpen,
  uiReady = true,
  activeHistoryId = null,
  searchQuery,
  setSearchQuery,
  onSelectHistory,
  onDeleteHistory,
  onShareHistory,
  onNewChat,
}: SidebarProps) {
  const { histories } = useChatHistory();
  const navigate = useNavigate();
  const location = useLocation();
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024);

  useEffect(() => {
    const handleResize = () => setIsDesktop(window.innerWidth >= 1024);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);
 
  const visibleHistories = useMemo(
    () => histories.filter((entry) => matchesSearch(entry, searchQuery)),
    [histories, searchQuery]
  );
 
  const toggleSidebar = () => setSidebarOpen?.(!sidebarOpen);
  
  const widthClosed = isDesktop ? SIDEBAR_WIDTH_COLLAPSED : 0;
 
  return (
    <motion.aside
      initial={enterOrSkip(uiReady, { width: widthClosed })}
      animate={{ width: sidebarOpen ? SIDEBAR_WIDTH_EXPANDED : widthClosed }}
      transition={sidebarWidthTransition}
      className="fixed lg:relative inset-y-0 lg:inset-auto left-0 z-50 lg:z-20 h-screen lg:h-full overflow-hidden bg-surface-container-low shadow-sm will-change-[width]"
    >
      <div
        className="relative h-full"
        style={{ width: SIDEBAR_WIDTH_EXPANDED }}
      >
        {/* Collapsed icon rail - Desktop only */}
        {isDesktop && (
          <motion.div
            aria-hidden={sidebarOpen}
            initial={false}
            animate={{ opacity: sidebarOpen ? 0 : 1 }}
            transition={{
              ...sidebarPanelTransition,
              delay: sidebarOpen ? 0 : 0.06,
            }}
            className={`absolute inset-y-0 left-0 flex w-[56px] flex-col items-center gap-2 py-4 ${
              sidebarOpen ? "pointer-events-none" : "pointer-events-auto"
            }`}
          >
            <RailButton label="Expand sidebar" onClick={toggleSidebar}>
              <Menu size={22} />
            </RailButton>
            <RailButton label="New chat" onClick={() => onNewChat?.()}>
              <Plus size={22} />
            </RailButton>
            <div className="flex-1" />
            <RailButton
              label="Account settings"
              active={location.pathname === ROUTES.account}
              onClick={() => navigate(ROUTES.account)}
            >
              <Settings size={22} />
            </RailButton>
          </motion.div>
        )}
 
        {/* Expanded panel */}
        <motion.div
          aria-hidden={!sidebarOpen}
          initial={false}
          animate={{
            opacity: sidebarOpen ? 1 : 0,
            x: sidebarOpen ? 0 : -8,
          }}
          transition={{
            ...sidebarPanelTransition,
            delay: sidebarOpen ? 0.05 : 0,
          }}
          className={`absolute inset-0 flex flex-col ${
            sidebarOpen ? "pointer-events-auto" : "pointer-events-none"
          }`}
        >
          <div className="shrink-0 flex items-center gap-2 px-4 pt-4 pb-3">
            <button
              type="button"
              onClick={toggleSidebar}
              aria-label="Collapse sidebar"
              aria-expanded={sidebarOpen}
              className={`${iconBtn} text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface`}
            >
              <Menu size={22} />
            </button>
            <div className="relative flex-1 min-w-0">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
                size={16}
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search chats..."
                tabIndex={sidebarOpen ? 0 : -1}
                className="w-full bg-surface-container-high/50 rounded pl-9 pr-3 py-2 text-sm text-on-surface placeholder:text-on-surface-variant/70 focus:ring-1 focus:ring-primary outline-none transition-all border-0"
              />
            </div>
          </div>

          <nav className="shrink-0 px-6 pt-5 flex flex-col gap-1.5 mb-5">
            {SIDEBAR_NAV.map((item) => (
              <SidebarNavLink
                key={item.to}
                label={item.label}
                icon={item.icon}
                active={location.pathname === item.to}
                onClick={() => navigate(item.to)}
              />
            ))}
          </nav>

          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-6 pr-4">
            <div className="mb-8">
              <button
                type="button"
                onClick={() => onNewChat?.()}
                className="w-full mb-3 flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-sm font-medium text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer bg-transparent"
              >
                <Plus size={16} />
                New chat
              </button>
              <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-bold mb-4 px-2">
                Chat history
              </h3>
              {visibleHistories.length > 0 ? (
                <div className="space-y-1">
                  {visibleHistories.map((entry) => (
                    <ChatHistoryItem
                      key={entry.id}
                      id={entry.id}
                      title={entry.title}
                      updatedAt={entry.updatedAt}
                      active={activeHistoryId === entry.id}
                      onSelect={() => {
                        onSelectHistory?.(entry.id);
                        navigate(ROUTES.home);
                      }}
                      onDelete={() => onDeleteHistory?.(entry.id)}
                      onShare={() => onShareHistory?.(entry.id)}
                    />
                  ))}
                </div>
              ) : (
                <p className="px-2 text-sm text-on-surface-variant">No chats match your search.</p>
              )}
            </div>
          </div>

          <div className="shrink-0 px-6 py-4 bg-surface-container-low">
            <button
              type="button"
              onClick={() => navigate(ROUTES.account)}
              className={`flex items-center gap-3 p-3 rounded-xl transition-all text-left w-full border-0 cursor-pointer ${
                location.pathname === ROUTES.account
                  ? "bg-primary/10 text-primary"
                  : "bg-transparent text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
              }`}
            >
              <Settings
                size={20}
                className={location.pathname === ROUTES.account ? "text-primary" : "text-secondary"}
              />
              <span className="text-sm font-semibold">Account</span>
            </button>
          </div>
        </motion.div>
      </div>
    </motion.aside>
  );
}
