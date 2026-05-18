/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from "react";
import { Monitor } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { SuggestionChip } from "./components/ui";
import { Sidebar, Header, PromptBar, TaskPanel, AiResponseCard } from "./components/layout";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [sentPrompt, setSentPrompt] = useState("");
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

  const sendPrompt = (text: string) => {
    if (text.trim()) {
      setSentPrompt(text);
      setIsSent(true);
      setPrompt("");
    }
  };

  const handleSend = () => {
    sendPrompt(prompt);
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

        <div className="flex-1 flex flex-col items-center px-6 h-full pt-12 overflow-y-auto custom-scrollbar pb-32">
          {!isSent ? (
            <div className="max-w-3xl w-full flex flex-col items-center gap-10">
              {/* Hero */}
              <div className="text-center">
                <h1 className="text-[56px] leading-[1.1] font-medium tracking-tight text-on-surface mb-4">
                  Welcome to Daffodil <br /> Intelligence
                </h1>
              </div>

              {/* Suggestions */}
              <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
                <SuggestionChip
                  text="Mood-based movie picker"
                  onClick={() => sendPrompt("Mood-based movie picker")}
                />
                <SuggestionChip
                  text="Trip packing checklist"
                  onClick={() => sendPrompt("Trip packing checklist")}
                />
                <SuggestionChip
                  text="E-commerce platform mockup"
                  onClick={() => sendPrompt("E-commerce platform mockup")}
                />
              </div>
            </div>
          ) : (
            <div className="w-full max-w-7xl h-full relative flex flex-col md:flex-row gap-6">
              {/* Left/Center Canvas: Open workspace canvas with dot pattern */}
              <div className="flex-1 flex items-center justify-center md:pr-[420px] min-h-[300px]">
                {/* Clean workspace area */}
              </div>
            </div>
          )}
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

        {/* Right Sidebar Panel: AI Response Card on top, Task Panel at the bottom */}
        <div className="fixed top-20 right-6 bottom-6 w-[calc(100%-48px)] sm:w-[360px] flex flex-col gap-4 z-30 pointer-events-none">
          {/* AI Response Card (only shows when isSent is true) */}
          <AnimatePresence>
            {isSent && (
              <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className="pointer-events-auto flex-shrink-0"
              >
                <AiResponseCard
                  prompt={sentPrompt}
                  onEdit={() => {
                    setPrompt(sentPrompt);
                    setTimeout(() => {
                      if (textareaRef.current) {
                        textareaRef.current.focus();
                        textareaRef.current.selectionStart = textareaRef.current.value.length;
                        textareaRef.current.selectionEnd = textareaRef.current.value.length;
                      }
                    }, 50);
                  }}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Task Panel (always sits at the bottom) */}
          <div className="pointer-events-auto mt-auto">
            <TaskPanel
              tasksCollapsed={tasksCollapsed}
              setTasksCollapsed={setTasksCollapsed}
            />
          </div>
        </div>

        {/* Desktop Indicator */}
        <div className="absolute bottom-6 left-8 z-20">
          <button className="p-2 text-on-surface-variant/50 hover:text-on-surface-variant transition-all">
            <Monitor size={20} />
          </button>
        </div>
      </main>
    </div>
  );
}