import { useState } from "react";
import { 
  Search,
  LayoutGrid,
  Users,
  Settings,
  HelpCircle,
  Mic,
  Cpu,
  Monitor,
  Brain
} from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { SidebarItem } from "../../ui";
import { recentProjects } from "./projects";
import { SidebarProps } from "./types";

export function Sidebar({ sidebarOpen }: SidebarProps) {
  const [projects] = useState(recentProjects);
  const navigate = useNavigate();

  return (
    <motion.aside
      initial={{ width: 0, x: -20 }}
      animate={{ width: sidebarOpen ? 280 : 0, x: sidebarOpen ? 0 : -20 }}
      exit={{ width: 0, x: -20 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed lg:relative inset-y-0 left-0 h-full glass-panel flex-shrink-0 z-50 overflow-hidden shadow-lg lg:shadow-none"
    >
      <div className="w-[280px] h-full flex flex-col p-6">
        <div className="flex items-center gap-3 mb-8">
          <span className="text-xl font-semibold tracking-tight">Daffodil Intelligence</span>
        </div>

        <div className="flex p-1 bg-surface-container-high rounded-xl mb-6">
          <button className="flex-1 flex items-center justify-center gap-2 bg-primary text-on-primary rounded-lg px-3 py-2 text-sm font-medium transition-all">
            <LayoutGrid size={18} />
            Projects
          </button>
          <button className="flex-1 flex items-center justify-center gap-2 text-on-surface-variant hover:text-on-surface px-3 py-2 text-sm transition-all">
            <Users size={18} />
            Shared
          </button>
        </div>

        <div className="relative mb-6">
          <Search className="absolute left-3 top-2.5 text-on-surface-variant" size={20} />
          <input 
            type="text" 
            placeholder="Search..."
            className="w-full bg-surface-container-high/50 border border-outline-variant/20 rounded-xl pl-10 pr-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant placeholder:text-on-surface-variant focus:ring-1 focus:ring-primary outline-none transition-all"
          />
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
          <div className="mb-8">
            <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-bold mb-4 px-2">Recent</h3>
            <div className="space-y-1">
              {projects.map(project => (
                <SidebarItem 
                  key={project.id}
                  title={project.title}
                  date={project.date}
                  img={project.img}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-outline-variant/20 flex flex-col gap-1">
          <button 
            onClick={() => navigate("/agents")}
            className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all text-left w-full border-0 bg-transparent cursor-pointer"
          >
            <Brain size={20} className="text-secondary" />
            <span className="text-sm font-semibold">Agents</span>
          </button>
          <button 
            onClick={() => navigate("/model")}
            className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all text-left w-full border-0 bg-transparent cursor-pointer"
          >
            <Settings size={20} className="text-primary" />
            <span className="text-sm font-semibold">Settings</span>
          </button>
          <button className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all text-left w-full border-0 bg-transparent cursor-pointer">
            <HelpCircle size={20} />
            <span className="text-sm">Help Center</span>
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
