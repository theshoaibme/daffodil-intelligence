import { useMemo } from "react";
import { Search, MessageSquare, Users, Settings, Plus } from "lucide-react";
import { motion } from "framer-motion";
import { useLocation, useNavigate } from "react-router-dom";
import { SidebarItem } from "../../ui";
import { ROUTES } from "../../../lib/routes";
import { sharedProjects } from "./projects";
import type { SidebarProps, SidebarTab } from "./types";

export type { SidebarProps } from "./types";
import { useLocalStorageState } from "../../../hooks/useLocalStorageState";
import { enterOrSkip } from "../../../lib/motion";
import { useChatHistory } from "../../../context/ChatHistoryContext";
import { ChatHistoryItem } from "./ChatHistoryItem";

function matchesSearch(item: { title: string; sharedBy?: string }, query: string) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  return (
    item.title.toLowerCase().includes(normalized) ||
    (item.sharedBy?.toLowerCase().includes(normalized) ?? false)
  );
}

export function Sidebar({
  sidebarOpen,
  uiReady = true,
  activeHistoryId = null,
  onSelectHistory,
  onDeleteHistory,
  onShareHistory,
  onNewChat,
}: SidebarProps) {
  const { histories } = useChatHistory();
  const [activeTab, setActiveTab] = useLocalStorageState<SidebarTab>(
    "di-dashboard-sidebar-tab",
    "projects"
  );
  const [searchQuery, setSearchQuery] = useLocalStorageState(
    "di-dashboard-sidebar-search",
    ""
  );
  const navigate = useNavigate();
  const location = useLocation();

  const visibleHistories = useMemo(
    () => histories.filter((entry) => matchesSearch(entry, searchQuery)),
    [histories, searchQuery]
  );

  const visibleShared = useMemo(
    () => sharedProjects.filter((project) => matchesSearch(project, searchQuery)),
    [searchQuery]
  );

  const sectionLabel = activeTab === "projects" ? "Chat history" : "Shared with you";
  const emptyLabel =
    activeTab === "projects"
      ? "No chats match your search."
      : "No shared chats match your search.";

  return (
    <motion.aside
      initial={enterOrSkip(uiReady, { width: 0, x: -20 })}
      animate={{ width: sidebarOpen ? 280 : 0, x: sidebarOpen ? 0 : -20 }}
      exit={{ width: 0, x: -20 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed inset-y-0 left-0 h-full glass-panel z-50 overflow-hidden shadow-lg"
    >
      <div className="w-[280px] h-full flex flex-col p-6">
        <div className="flex items-center gap-3 mb-8">
          <span className="text-xl font-semibold tracking-tight">Daffodil Intelligence</span>
        </div>

        <div className="flex p-1 bg-surface-container-high rounded-xl mb-6">
          <button
            type="button"
            onClick={() => setActiveTab("projects")}
            className={`flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
              activeTab === "projects"
                ? "bg-primary text-on-primary"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
          >
            <MessageSquare size={18} />
            Chats
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("shared")}
            className={`flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
              activeTab === "shared"
                ? "bg-primary text-on-primary"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
          >
            <Users size={18} />
            Shared
          </button>
        </div>

        <div className="relative mb-6">
          <Search className="absolute left-3 top-2.5 text-on-surface-variant" size={20} />
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder={activeTab === "projects" ? "Search chats..." : "Search shared..."}
            className="w-full bg-surface-container-high/50 border border-outline-variant/20 rounded-xl pl-10 pr-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant placeholder:text-on-surface-variant focus:ring-1 focus:ring-primary outline-none transition-all"
          />
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
          <div className="mb-8">
            {activeTab === "projects" && (
              <button
                type="button"
                onClick={() => onNewChat?.()}
                className="w-full mb-3 flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-outline-variant/30 text-sm font-medium text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer bg-transparent"
              >
                <Plus size={16} />
                New chat
              </button>
            )}
            <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-bold mb-4 px-2">
              {sectionLabel}
            </h3>
            {activeTab === "projects" ? (
              visibleHistories.length > 0 ? (
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
                <p className="px-2 text-sm text-on-surface-variant">{emptyLabel}</p>
              )
            ) : visibleShared.length > 0 ? (
              <div className="space-y-1">
                {visibleShared.map((project) => (
                  <SidebarItem
                    key={project.id}
                    title={project.title}
                    date={project.date}
                    img={project.img}
                    subtitle={project.sharedBy}
                    onClick={() => navigate(ROUTES.home)}
                  />
                ))}
              </div>
            ) : (
              <p className="px-2 text-sm text-on-surface-variant">{emptyLabel}</p>
            )}
          </div>
        </div>

        <div className="pt-4 border-t border-outline-variant/20">
          <button
            type="button"
            onClick={() => navigate(ROUTES.account)}
            className={`flex items-center gap-3 p-3 rounded-xl transition-all text-left w-full border-0 cursor-pointer ${
              location.pathname === ROUTES.account
                ? "bg-primary/10 text-primary"
                : "bg-transparent text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
            }`}
          >
            <Settings size={20} className={location.pathname === ROUTES.account ? "text-primary" : "text-secondary"} />
            <span className="text-sm font-semibold">Account</span>
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
