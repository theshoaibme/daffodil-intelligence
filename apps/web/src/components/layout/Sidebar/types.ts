export interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen?: (open: boolean) => void;
  uiReady?: boolean;
  activeHistoryId?: string | null;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSelectHistory?: (id: string) => void;
  onDeleteHistory?: (id: string) => void;
  onShareHistory?: (id: string) => Promise<void>;
  onNewChat?: () => void;
  agentModeActive?: boolean;
  onAgentsClick?: () => void;
}
