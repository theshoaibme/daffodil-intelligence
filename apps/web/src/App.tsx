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
import { ROUTES } from "./lib/routes";

import { Routes, Route, useNavigate, Navigate } from "react-router-dom";
import {
  ModelManagementPage,
  LiveVoicePage,
  AgentDashboard,
  ComputerView,
  AuthTelegramPage,
  LoginPage,
  RegisterPage,
  GuidancePage,
  GoogleCallbackPage,
  SettingsPage,
  LandingPage,
} from "./components/layout";
import { ProtectedRoute } from "./components/auth";

const LEGACY_REDIRECTS: { from: string; to: string }[] = [
  { from: "/intelligence/login", to: ROUTES.login },
  { from: "/intelligence/register", to: ROUTES.register },
  { from: "/guidance", to: ROUTES.guidance },
  { from: "/settings", to: ROUTES.settings },
  { from: "/agents", to: ROUTES.agents },
  { from: "/live", to: ROUTES.live },
  { from: "/computer", to: ROUTES.computer },
  { from: "/model", to: ROUTES.model },
  { from: "/auth/google/callback", to: ROUTES.googleCallback },
  { from: "/auth/telegram", to: ROUTES.telegramAuth },
];

export default function App() {
  return (
    <Routes>
      <Route path={ROUTES.landing} element={<LandingPage />} />
      {LEGACY_REDIRECTS.map(({ from, to }) => (
        <Route key={from} path={from} element={<Navigate to={to} replace />} />
      ))}

      <Route path={ROUTES.home} element={<ChatDashboard />} />
      <Route path={ROUTES.model} element={<ModelManagementPage />} />
      <Route path={ROUTES.live} element={<LiveVoicePage />} />
      <Route path={ROUTES.agents} element={<AgentDashboard />} />
      <Route path={ROUTES.computer} element={<ComputerView />} />
      <Route path={ROUTES.login} element={<LoginPage />} />
      <Route path={ROUTES.register} element={<RegisterPage />} />
      <Route path={ROUTES.googleCallback} element={<GoogleCallbackPage />} />
      <Route path={ROUTES.telegramAuth} element={<AuthTelegramPage />} />
      <Route
        path={ROUTES.guidance}
        element={
          <ProtectedRoute>
            <GuidancePage />
          </ProtectedRoute>
        }
      />
      <Route path={ROUTES.settings} element={<SettingsPage />} />
    </Routes>
  );
}

function ChatDashboard() {
  const navigate = useNavigate();
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
  const lastUserMessage = messages.filter((m) => m.role === "user").pop();
  const lastAssistantMessage = messages.filter((m) => m.role === "assistant").pop();

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
        textareaRef.current?.focus();
      }, 50);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden relative font-sans">
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <>
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

      <main className="flex-1 flex flex-col relative overflow-hidden bg-background dot-pattern transition-all">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <div className="flex-1 flex flex-col items-center px-6 h-full pt-12 overflow-y-auto custom-scrollbar pb-32">
          {!hasMessages ? (
            <div className="max-w-3xl w-full flex flex-col items-center gap-10">
              <div className="text-center px-4">
                <h1 className="text-4xl sm:text-[56px] leading-[1.1] font-medium tracking-tight text-on-surface mb-4">
                  Welcome to Daffodil <br className="hidden sm:inline" /> Intelligence
                </h1>
              </div>

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
              <div className="flex-1 w-full flex items-center justify-center md:pr-[420px] min-h-[180px] md:min-h-[300px]" />

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

        <div className="hidden md:flex fixed top-20 right-6 bottom-6 w-[360px] flex-col gap-4 z-30 pointer-events-none">
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

          <div className="pointer-events-auto mt-auto">
            <TaskPanel
              tasksCollapsed={tasksCollapsed}
              setTasksCollapsed={setTasksCollapsed}
            />
          </div>
        </div>

        <div className="absolute bottom-6 left-8 z-20">
          <button
            type="button"
            onClick={() => navigate(ROUTES.computer)}
            className="p-2 text-on-surface-variant/50 hover:text-on-surface-variant transition-all"
            aria-label="Open computer view"
          >
            <Monitor size={20} />
          </button>
        </div>
      </main>
    </div>
  );
}
