/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from "react";
import { Monitor } from "lucide-react";
import { AnimatePresence } from "framer-motion";
import { SuggestionChip } from "./components/ui";
import { Sidebar, Header, PromptBar, TaskPanel } from "./components/layout";

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

      {/* Sidebar with AnimatePresence */}
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-background dot-pattern transition-all">
        {/* Header */}
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

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
        <PromptBar
          prompt={prompt}
          setPrompt={setPrompt}
          isSent={isSent}
          handleSend={handleSend}
          plusMenuOpen={plusMenuOpen}
          setPlusMenuOpen={setPlusMenuOpen}
          textareaRef={textareaRef}
        />

        {/* Task Panel (Bottom Left) */}
        <TaskPanel
          isSent={isSent}
          tasksCollapsed={tasksCollapsed}
          setTasksCollapsed={setTasksCollapsed}
        />

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