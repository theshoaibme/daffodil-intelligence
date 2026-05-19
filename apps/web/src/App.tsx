/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from "react";
import { Monitor } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { SuggestionChip } from "./components/ui";
import { Sidebar, Header, PromptBar, TaskPanel, AiResponseCard } from "./components/layout";
import { useChat } from "./hooks/useChat";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [tasksCollapsed, setTasksCollapsed] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { 
    messages, 
    isLoading, 
    isStreaming, 
    thinkingSteps,
    error,
    send,
  } = useChat();

  const hasMessages = messages.length > 0;
  const lastUserMessage = messages.filter(m => m.role === "user").pop();
  const lastAssistantMessage = messages.filter(m => m.role === "assistant").pop();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [prompt]);

  const sendPrompt = async (text: string) => {
    if (text.trim()) {
      setPrompt("");
      await send(text);
    }
  };

  const handleSend = () => {
    sendPrompt(prompt);
  };

  const handleEdit = () => {
    if (lastUserMessage) {
      setPrompt(lastUserMessage.content);
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 50);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden relative font-sans">
      {/* Sidebar with AnimatePresence */}
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <>
            {/* Backdrop overlay for mobile */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              className="fixed inset-0 bg-background/50 backdrop-blur-sm z-45 lg:hidden"
            />
            <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-background dot-pattern transition-all">
        {/* Header */}
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <div className="flex-1 flex flex-col items-center px-6 h-full pt-12 overflow-y-auto custom-scrollbar pb-32">
          {!hasMessages ? (
            <div className="max-w-3xl w-full flex flex-col items-center gap-10">
              {/* Hero */}
              <div className="text-center px-4">
                <h1 className="text-4xl sm:text-[56px] leading-[1.1] font-medium tracking-tight text-on-surface mb-4">
                  Welcome to Daffodil <br className="hidden sm:inline" /> Intelligence
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
            <div className="w-full max-w-7xl relative flex flex-col md:flex-row gap-6 items-center md:items-start justify-center">
              {/* Left/Center Canvas: Open workspace canvas with dot pattern */}
              <div className="flex-1 w-full flex items-center justify-center md:pr-[420px] min-h-[180px] md:min-h-[300px]">
                {/* Clean workspace area */}
              </div>

              {/* Mobile View Stack: Stack AI Card and Task Panel below the Canvas on small viewports */}
              <div className="w-full max-w-md flex flex-col gap-4 md:hidden pb-8">
                <AiResponseCard
                  prompt={lastUserMessage?.content || ""}
                  response={lastAssistantMessage?.content || ""}
                  isStreaming={isStreaming}
                  thinkingSteps={thinkingSteps}
                  isThinking={isStreaming}
                  onEdit={handleEdit}
                  error={error}
                />
                <TaskPanel
                  tasksCollapsed={tasksCollapsed}
                  setTasksCollapsed={setTasksCollapsed}
                />
              </div>
            </div>
          )}
        </div>

        {/* Prompt Bar Overlay */}
        <PromptBar
          prompt={prompt}
          setPrompt={setPrompt}
          isSent={hasMessages}
          handleSend={handleSend}
          plusMenuOpen={plusMenuOpen}
          setPlusMenuOpen={setPlusMenuOpen}
          textareaRef={textareaRef}
          isLoading={isLoading || isStreaming}
        />

        {/* Right Sidebar Panel: AI Response Card on top, Task Panel at the bottom */}
        <div className="hidden md:flex fixed top-20 right-6 bottom-6 w-[360px] flex-col gap-4 z-30 pointer-events-none">
          {/* AI Response Card (only shows when hasMessages is true) */}
          <AnimatePresence>
            {hasMessages && (
              <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className="pointer-events-auto flex-shrink-0"
              >
                <AiResponseCard
                  prompt={lastUserMessage?.content || ""}
                  response={lastAssistantMessage?.content || ""}
                  isStreaming={isStreaming}
                  thinkingSteps={thinkingSteps}
                  isThinking={isStreaming}
                  onEdit={handleEdit}
                  error={error}
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