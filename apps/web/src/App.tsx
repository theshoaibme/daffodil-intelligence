/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { enterOrSkip, modeSpring, overlayFade } from "./lib/motion";
import { UiAnimationProvider, useUiAnimationReady } from "./context/UiAnimationContext";
import { ChatHistoryProvider, useChatHistory } from "./context/ChatHistoryContext";
import { getHistoryEntry } from "./lib/chatHistoryStorage";
import { SuggestionChip } from "./components/ui";
import { Sidebar, Header, PromptBar, TaskPanel, AiResponseCard } from "./components/layout";
import { useChat } from "./hooks/useChat";
import { useLocalStorageState } from "./hooks/useLocalStorageState";
import { ROUTES } from "./lib/routes";

import { Routes, Route, Navigate, useSearchParams } from "react-router-dom";
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
  AccountPage,
  LandingPage,
  TermsPage,
  PrivacyPage,
} from "./components/layout";
import { ProtectedRoute } from "./components/auth";

const LEGACY_REDIRECTS: { from: string; to: string }[] = [
  { from: "/intelligence/login", to: ROUTES.login },
  { from: "/intelligence/register", to: ROUTES.register },
  { from: "/guidance", to: ROUTES.guidance },
  { from: "/settings", to: ROUTES.account },
  { from: "/intelligence/settings", to: ROUTES.account },
  { from: "/intelligence/accounts", to: ROUTES.account },
  { from: "/intelligence/account", to: ROUTES.account },
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

      <Route path={ROUTES.login} element={<LoginPage />} />
      <Route path={ROUTES.register} element={<RegisterPage />} />
      <Route path={ROUTES.terms} element={<TermsPage />} />
      <Route path={ROUTES.privacy} element={<PrivacyPage />} />
      <Route path={ROUTES.googleCallback} element={<GoogleCallbackPage />} />
      <Route path={ROUTES.telegramAuth} element={<AuthTelegramPage />} />

      <Route element={<ProtectedRoute />}>
        <Route
          path={ROUTES.home}
          element={
            <UiAnimationProvider>
              <ChatHistoryProvider>
                <ChatDashboard />
              </ChatHistoryProvider>
            </UiAnimationProvider>
          }
        />
        <Route path={ROUTES.model} element={<ModelManagementPage />} />
        <Route path={ROUTES.live} element={<LiveVoicePage />} />
        <Route path={ROUTES.agents} element={<AgentDashboard />} />
        <Route path={ROUTES.computer} element={<ComputerView />} />
        <Route path={ROUTES.guidance} element={<GuidancePage />} />
        <Route path={ROUTES.account} element={<AccountPage />} />
      </Route>
    </Routes>
  );
}

const DASHBOARD_STORAGE_KEYS = {
  sidebarOpen: "di-dashboard-sidebar-open",
  tasksCollapsed: "di-dashboard-tasks-collapsed",
  promptDraft: "di-dashboard-prompt-draft",
} as const;

function ChatDashboard() {
  const uiReady = useUiAnimationReady();
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    activeHistoryId,
    syncActiveSession,
    selectHistory,
    startNewChat,
    deleteHistory,
    shareHistory,
  } = useChatHistory();
  const [sidebarOpen, setSidebarOpen] = useLocalStorageState(
    DASHBOARD_STORAGE_KEYS.sidebarOpen,
    true
  );
  const [copycatMode, setCopycatMode] = useState(false);
  const [prompt, setPrompt] = useLocalStorageState(DASHBOARD_STORAGE_KEYS.promptDraft, "");
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [tasksCollapsed, setTasksCollapsed] = useLocalStorageState(
    DASHBOARD_STORAGE_KEYS.tasksCollapsed,
    false
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const handledChatParam = useRef(false);

  const initialSession = activeHistoryId ? getHistoryEntry(activeHistoryId) : null;
  const {
    chatId,
    messages,
    isLoading,
    isStreaming,
    thinkingSteps,
    error,
    send,
    loadSession,
  } = useChat({
    initialChatId: initialSession?.chatId ?? null,
    initialMessages: initialSession?.messages ?? [],
  });

  useEffect(() => {
    if (isStreaming) return;
    syncActiveSession(chatId, messages);
  }, [chatId, messages, isStreaming, syncActiveSession]);

  useEffect(() => {
    if (handledChatParam.current) return;
    const chatParam = searchParams.get("chat");
    if (!chatParam) return;

    handledChatParam.current = true;
    const session = selectHistory(chatParam);
    loadSession(session.chatId, session.messages);
    setSearchParams({}, { replace: true });
  }, [searchParams, selectHistory, loadSession, setSearchParams]);

  const handleSelectHistory = (id: string) => {
    const session = selectHistory(id);
    loadSession(session.chatId, session.messages);
  };

  const handleNewChat = () => {
    const session = startNewChat();
    loadSession(session.chatId, session.messages);
    setPrompt("");
  };

  const handleDeleteHistory = (id: string) => {
    const wasActive = activeHistoryId === id;
    deleteHistory(id);
    if (wasActive) {
      loadSession(null, []);
      setPrompt("");
    }
  };

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
    if (!text.trim()) return;

    if (!activeHistoryId) {
      const session = startNewChat();
      loadSession(session.chatId, session.messages);
    }

    setPrompt("");
    await send(text);
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
              initial={enterOrSkip(uiReady, { opacity: 0 })}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setSidebarOpen(false)}
              className="fixed inset-0 bg-background/50 backdrop-blur-sm z-45 lg:hidden"
            />
            <Sidebar
              sidebarOpen={sidebarOpen}
              setSidebarOpen={setSidebarOpen}
              uiReady={uiReady}
              activeHistoryId={activeHistoryId}
              onSelectHistory={handleSelectHistory}
              onDeleteHistory={handleDeleteHistory}
              onShareHistory={shareHistory}
              onNewChat={handleNewChat}
            />
          </>
        )}
      </AnimatePresence>

      <main className="flex-1 flex flex-col relative overflow-hidden bg-background dot-pattern">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <motion.div
          className="flex-1 flex flex-col items-center px-6 h-full pt-12 overflow-y-auto custom-scrollbar pb-32"
          animate={{
            opacity: copycatMode ? 0.35 : 1,
            scale: copycatMode ? 0.985 : 1,
            filter: copycatMode ? "blur(6px)" : "blur(0px)",
          }}
          transition={overlayFade}
          style={{ pointerEvents: copycatMode ? "none" : "auto" }}
        >
          {!hasMessages ? (
            <div className="fixed inset-x-0 top-16 bottom-32 z-10 flex flex-col items-center justify-center px-6 pointer-events-none">
              <div className="max-w-3xl w-full flex flex-col items-center gap-10 pointer-events-auto">
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
            </div>
          ) : (
            <div className="w-full max-w-7xl relative flex flex-col md:flex-row gap-6 items-center md:items-start justify-center">
              <div className="flex-1 w-full flex items-center justify-center md:pr-[420px] min-h-[180px] md:min-h-[300px]" />

              <div className="w-full max-w-md flex flex-col gap-4 md:hidden pb-36">
                <AiResponseCard
                  prompt={lastUserMessage?.content || ""}
                  response={lastAssistantMessage?.content || ""}
                  isStreaming={isStreaming}
                  thinkingSteps={thinkingSteps}
                  isThinking={isStreaming}
                  onEdit={handleEdit}
                  error={error}
                />
              </div>
            </div>
          )}
        </motion.div>

        <LayoutGroup id="mode-switch">
          <AnimatePresence mode="popLayout">
            {!copycatMode && (
              <PromptBar
                key="chat-mode-bar"
                uiReady={uiReady}
                prompt={prompt}
                setPrompt={setPrompt}
                isSent={hasMessages}
                handleSend={handleSend}
                plusMenuOpen={plusMenuOpen}
                setPlusMenuOpen={setPlusMenuOpen}
                textareaRef={textareaRef}
                isLoading={isLoading || isStreaming}
                onCopycatMode={() => setCopycatMode(true)}
                copycatActive={copycatMode}
              />
            )}
          </AnimatePresence>

          <AnimatePresence>
            {copycatMode && (
              <ComputerView
                key="copycat-mode"
                embedded
                onExitCopycat={() => setCopycatMode(false)}
              />
            )}
          </AnimatePresence>
        </LayoutGroup>

        <motion.div
          className="hidden md:flex fixed top-20 right-6 bottom-6 w-[360px] flex-col gap-4 z-30 pointer-events-none"
          animate={{
            opacity: copycatMode ? 0 : 1,
            x: copycatMode ? 24 : 0,
          }}
          transition={modeSpring}
        >
          <AnimatePresence>
            {hasMessages && (
              <motion.div
                initial={enterOrSkip(uiReady, { opacity: 0, y: -20, scale: 0.95 })}
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
              uiReady={uiReady}
            />
          </div>
        </motion.div>

        <div className="md:hidden fixed bottom-28 left-0 right-0 z-20 flex justify-center px-4 pointer-events-none">
          <div className="w-full max-w-md pointer-events-auto">
            <TaskPanel
              tasksCollapsed={tasksCollapsed}
              setTasksCollapsed={setTasksCollapsed}
              uiReady={uiReady}
            />
          </div>
        </div>

      </main>
    </div>
  );
}
