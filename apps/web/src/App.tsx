/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from "react";
import { 
  Menu, 
  FileText, 
  MessageSquare, 
  Gift, 
  Plus, 
  ImagePlus, 
  ChevronDown, 
  ArrowUp, 
  Sparkles, 
  Monitor, 
  CheckCircle2, 
  Compass, 
  ChevronUp,
  Search,
  LayoutGrid,
  Users,
  Settings,
  HelpCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { SidebarItem, HeaderIcon, SuggestionChip, LogItem, DropdownItem } from "./components/ui";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [isSent, setIsSent] = useState(false);
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [tasksCollapsed, setTasksCollapsed] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [prompt]);

  const handleSend = () => {
    if (prompt.trim()) {
      setIsSent(true);
      // In a real app, this would trigger the AI response
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden relative font-sans">
      {/* Sidebar Hover Zone - Invisible hover trigger on the left edge */}
      <div 
        className="fixed inset-y-0 left-0 w-2 z-[60] group cursor-pointer lg:hidden"
        onMouseEnter={() => setSidebarOpen(true)}
      />

      {/* Sidebar */}
      <AnimatePresence mode="wait">
        <motion.aside
          initial={false}
          animate={{ width: sidebarOpen ? 280 : 0, x: sidebarOpen ? 0 : -20 }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="h-full glass-panel border-r border-outline-variant/30 flex-shrink-0 z-50 overflow-hidden relative shadow-lg"
          onMouseLeave={() => {
            // Only auto-close if not locked/clicked or if on smaller screens
            if (window.innerWidth < 1024) setSidebarOpen(false);
          }}
        >
          <div className="w-[280px] h-full flex flex-col p-6">
          <div className="flex items-center gap-3 mb-8">
            <span className="text-xl font-semibold tracking-tight">Stitch</span>
            <span className="bg-primary/20 text-primary text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider">BETA</span>
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
              className="w-full bg-surface-container-high/50 border border-outline-variant/20 rounded-xl pl-10 pr-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant focus:ring-1 focus:ring-primary outline-none transition-all"
            />
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
            <div className="mb-8">
              <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-bold mb-4 px-2">Recent</h3>
              <div className="space-y-1">
                <SidebarItem 
                  title="DIU ThesisHub" 
                  date="Apr 19" 
                  img="https://lh3.googleusercontent.com/aida-public/AB6AXuCY5eqAPODPEeagpATFByto0n2e_2koITihdNgcLx0NJgoNNGsbLsw7zxUh8Uep7rHGkYOV3-PRcd9jYbEw0pU2jH4esxm7iufR9ecFV34-b5A428hFHqnw8D1VQ9WNp51iCPD0r6IiCFdw7DE2AU6Xmq1kQE6fv63xjy2BTMbduqDTbN9cZbQpgzHaNBwUtHPG_duNEOHieK_9CRIp8vMS8HN01g_0irDrvtycAJLSwTeuSoje_kWFql3_XhNEQUV9y4taT3CLQA"
                />
                <SidebarItem 
                  title="UniProject Hub" 
                  date="Apr 18" 
                  img="https://lh3.googleusercontent.com/aida-public/AB6AXuDc-araT87kcIu473N3I11_qScEJnrXw-u2yN0w62o_1EKLIx1Dc942y1I03rHMT4wZkShFqZ2s3IbL9j19CitwySAweTynVhyGY-NmroI1GfjEkDw7I7AQ_sOMAuPXbdfvw-slakQ1yXoND8bGKTSWg-KlK-3BWpVd0OFEsgIORHM_OgRQvBtMYlA3s_VeAPeWYq6bhKAvkTRhk72gahTGDR4tXpanx5hdYAeADyfWiwD2kdPK8-IBY7DfiTD0Lsq53yAbNpXwzA"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-outline-variant/20 flex flex-col gap-1">
            <button className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all">
              <Settings size={20} />
              <span className="text-sm">Settings</span>
            </button>
            <button className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all">
              <HelpCircle size={20} />
              <span className="text-sm">Help Center</span>
            </button>
          </div>
        </div>
      </motion.aside>
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-background dot-pattern transition-all">
        {/* Header */}
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

        <div className="flex-1 flex flex-col items-center px-6 h-full pt-12">
          <div className="max-w-3xl w-full flex flex-col items-center gap-10">
            {/* Hero */}
            <div className="text-center">
              <h1 className="text-[56px] leading-[1.1] font-medium tracking-tight text-on-surface mb-4">
                Welcome to Daffodil <br /> Intelligence
              </h1>
            </div>

            {/* Suggestions */}
            <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
              <SuggestionChip text="Mood-based movie picker" />
              <SuggestionChip text="Trip packing checklist" />
              <SuggestionChip text="E-commerce platform mockup" />
            </div>
          </div>
        </div>

        {/* Prompt Bar Overlay */}
        <motion.div 
          layout
          className={`fixed transition-all z-50 transform flex justify-center w-full px-4 ${isSent ? 'bottom-6 left-6 max-w-[480px] justify-start' : 'bottom-6 left-0'}`}
        >
          <div className="w-full max-w-2xl bg-surface-container-high/40 backdrop-blur-xl border border-outline-variant/40 flex flex-col gap-2 rounded-3xl p-3 relative shadow-md">
            {/* Plus Menu Popup */}
            <AnimatePresence>
              {plusMenuOpen && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: 10 }}
                  className="absolute bottom-full left-3 mb-4 w-56 bg-surface-container-high/95 backdrop-blur-2xl border border-outline-variant/40 rounded-2xl shadow-md z-[60]"
                >
                  <div className="p-2 space-y-1">
                    <DropdownItem icon={<Compass className="text-primary" size={20} />} text="MCP" />
                    <DropdownItem icon={<Monitor className="text-primary" size={20} />} text="Agent" />
                    <DropdownItem icon={<Compass className="text-primary" size={20} />} text="Research" />
                    <DropdownItem icon={<CheckCircle2 className="text-primary" size={20} />} text="Task" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <textarea 
              ref={textareaRef}
              rows={1}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="What would you like to change or create?"
              className="w-full bg-transparent border-none outline-none resize-none text-base text-on-surface placeholder-on-surface-variant focus:ring-0 p-2 leading-relaxed max-h-[200px]"
            />

            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-1">
                <button 
                  onClick={() => setPlusMenuOpen(!plusMenuOpen)}
                  className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest rounded-full transition-all"
                >
                  <Plus size={22} />
                </button>
                <button className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest rounded-full transition-all">
                  <ImagePlus size={22} />
                </button>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 bg-surface-container-highest/60 hover:bg-surface-container-highest px-3 py-1.5 border border-outline-variant/20 cursor-pointer transition-colors rounded-full lg:flex hidden">
                  <div className="w-5 h-5 rounded-full bg-primary border border-black/20"></div>
                  <span className="text-xs font-medium text-on-surface-variant">Gemini</span>
                  <ChevronDown size={14} className="text-on-surface-variant" />
                </div>
                <button className="flex items-center gap-2 bg-surface-container-highest/60 hover:bg-surface-container-highest px-4 py-2 text-on-surface transition-colors border border-outline-variant/20 rounded-full">
                  <span className="text-xs font-medium">3 Flash</span>
                  <ChevronDown size={14} />
                </button>
                <button className="w-10 h-10 flex items-center justify-center bg-primary/10 text-primary hover:bg-primary/20 rounded-full transition-all">
                  <Sparkles size={20} fill="currentColor" />
                </button>
                <button 
                  onClick={handleSend}
                  className="w-10 h-10 flex items-center justify-center bg-primary text-on-primary rounded-full hover:opacity-90 transition-all font-bold"
                >
                  <ArrowUp size={22} strokeWidth={3} />
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Task Panel (Bottom Left) */}
        {!isSent && (
          <div className="fixed bottom-6 left-6 w-[320px] bg-surface-container-high/90 backdrop-blur-xl border border-outline-variant/40 shadow-md z-30 flex flex-col overflow-hidden rounded-3xl" id="agent-log-panel">
            {/* Panel Body */}
            {tasksCollapsed ? (
              <div className="p-3 border-b border-outline-variant/20">
                <LogItem text="Refine the sidebar collapse ..." active />
              </div>
            ) : (
              <div className="flex-1 p-4 custom-scrollbar max-h-[300px] overflow-y-auto space-y-2.5">
                <LogItem text="also right sling create div in r..." />
                <LogItem text="Refine the sidebar collapse ..." active />
                <LogItem text="Implement a sticky sidebar b..." />
                <LogItem text="Make the chat input dynami..." />
                <LogItem text="Make the chat input dynami..." />
              </div>
            )}
            
            {/* Panel Header */}
            <div className="flex items-center justify-between border-t border-outline-variant/20 bg-surface-container-highest/20 p-3">
              <div className="flex items-center gap-2">
                <Compass size={20} className="text-primary" />
                <span className="text-sm font-semibold text-on-surface">Task</span>
              </div>
              <button 
                onClick={() => setTasksCollapsed(!tasksCollapsed)}
                className="p-1 hover:bg-surface-container-highest rounded-md transition-colors text-on-surface-variant"
              >
                {tasksCollapsed ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>
            </div>
          </div>
        )}

        {/* Desktop Indicator */}
        <div className="absolute bottom-6 right-8">
          <button className="p-2 text-on-surface-variant/50 hover:text-on-surface-variant transition-all">
            <Monitor size={20} />
          </button>
        </div>
      </main>
    </div>
  );
}