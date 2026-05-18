import { Menu, FileText, MessageSquare, Gift } from "lucide-react";
import { HeaderIcon } from "../ui";

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export function Header({ sidebarOpen, setSidebarOpen }: HeaderProps) {
  return (
    <header className="flex justify-between items-center h-16 px-8 w-full z-20">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-surface-container-highest rounded-full transition-colors text-on-surface-variant"
        >
          <Menu size={24} />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <HeaderIcon title="Documentation" icon={<FileText size={22} />} />
          <HeaderIcon title="Feedback" icon={<MessageSquare size={22} />} />
          <HeaderIcon title="What's new" icon={<Gift size={22} />} />
        </div>
        <div className="w-8 h-8 rounded-full overflow-hidden border border-outline-variant/30 ml-2">
          <img 
            alt="User profile" 
            className="w-full h-full object-cover" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ" 
          />
        </div>
      </div>
    </header>
  );
}
