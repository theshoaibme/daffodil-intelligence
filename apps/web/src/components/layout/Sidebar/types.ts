export interface SidebarProject {
  id: string;
  title: string;
  date: string;
  img: string;
}

export interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}
