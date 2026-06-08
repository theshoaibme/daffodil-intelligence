export type SidebarTab = "projects" | "shared";

export interface SidebarProject {
  id: string;
  title: string;
  date: string;
  img: string;
  sharedBy?: string;
}

export interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}
