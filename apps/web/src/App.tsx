/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { enterOrSkip, modeSpring, overlayFade } from "./lib/motion";
import { UiAnimationProvider, useUiAnimationReady } from "./context/UiAnimationContext";
import { ChatHistoryProvider, useChatHistory } from "./context/ChatHistoryContext";
import { getHistoryEntry } from "./lib/chatHistoryStorage";
import { SuggestionChip } from "./components/ui";
import { Sidebar, Header, PromptBar, TaskPanel, AiResponseCard } from "./components/layout";
import type { TaskItem } from "./components/layout/TaskPanel/TaskPanel";
import type { ParallelSimulationState } from "./components/layout/AgentDashboard/parallelSimulator";
import { useChat } from "./hooks/useChat";
import { useLocalStorageState } from "./hooks/useLocalStorageState";
import { useAuth } from "./context/AuthContext";
import { ROUTES } from "./lib/routes";

import { Routes, Route, Navigate, useSearchParams, useNavigate } from "react-router-dom";
import {
  ModelManagementPage,
  LiveVoicePage,
  AgentDashboard,
  ComputerView,
  AuthTelegramPage,
  LoginPage,
  RegisterPage,
  GuidancePage,
  SkillsPage,
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
        <Route path={ROUTES.agents} element={<Navigate to={`${ROUTES.home}?agents=1`} replace />} />
        <Route path={ROUTES.skills} element={<SkillsPage />} />
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
  selectedTools: "di-dashboard-selected-tools",
} as const;

/** Horizontal column width — shared by welcome hero and prompt bar. */
const MAIN_COLUMN = "w-full max-w-xl mx-auto";

/** Fills main below header; pb reserves prompt bar (bottom-6 + bar height). */
const MAIN_STAGE =
  "absolute inset-0 flex items-center justify-center px-4 pb-[8.5rem] pointer-events-none";

/** Prompt bar slot — pinned to bottom of main stage, same horizontal axis as hero. */
const PROMPT_SLOT =
  "absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-30 pointer-events-none";

function greetingDisplayName(fullName: string | null | undefined, email: string): string {
  if (fullName?.trim()) return fullName.trim();
  const local = email.split("@")[0]?.trim();
  return local || "there";
}

function ChatDashboard() {
  const uiReady = useUiAnimationReady();
  const { user } = useAuth();
  const navigate = useNavigate();
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
  const [searchQuery, setSearchQuery] = useLocalStorageState(
    "di-dashboard-sidebar-search",
    ""
  );
  const [copycatMode, setCopycatMode] = useState(false);
  const [agentViewOpen, setAgentViewOpen] = useState(false);
  const [selectedTools, setSelectedTools] = useLocalStorageState<string[]>(
    DASHBOARD_STORAGE_KEYS.selectedTools,
    ["Agent", "Task"]
  );
  const [prompt, setPrompt] = useLocalStorageState(DASHBOARD_STORAGE_KEYS.promptDraft, "");
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [tasksCollapsed, setTasksCollapsed] = useLocalStorageState(
    DASHBOARD_STORAGE_KEYS.tasksCollapsed,
    false
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const handledChatParam = useRef(false);
  const handledAgentsParam = useRef(false);
  const [agentLiveTasks, setAgentLiveTasks] = useState<TaskItem[] | null>(null);

  const agentModeActive = selectedTools.includes("Agent") && !copycatMode;

  const handleToggleTool = (tool: string) => {
    setSelectedTools((prev) => {
      const next = prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool];
      if (tool === "Agent") {
        setAgentViewOpen(next.includes("Agent"));
      }
      return next;
    });
  };

  const handleAgentsNav = () => {
    navigate(ROUTES.home);
    setSelectedTools((prev) =>
      prev.includes("Agent") ? prev : [...prev, "Agent"]
    );
    setAgentViewOpen(true);
  };

  const handleCloseAgentView = () => {
    setAgentViewOpen(false);
    setSelectedTools((prev) => prev.filter((t) => t !== "Agent"));
  };

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

  useEffect(() => {
    if (handledAgentsParam.current) return;
    if (searchParams.get("agents") !== "1") return;

    handledAgentsParam.current = true;
    setSelectedTools((prev) =>
      prev.includes("Agent") ? prev : [...prev, "Agent"]
    );
    setAgentViewOpen(true);
    setSearchParams({}, { replace: true });
  }, [searchParams, setSearchParams, setSelectedTools]);

  const handleSelectHistory = (id: string) => {
    const session = selectHistory(id);
    loadSession(session.chatId, session.messages);
  };

  const handleNewChat = () => {
    const session = startNewChat();
    loadSession(session.chatId, session.messages);
    setPrompt("");
    setAgentViewOpen(false);
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
  const showAgentDashboard = agentModeActive && (hasMessages || agentViewOpen);
  const lastUserMessage = messages.filter((m) => m.role === "user").pop();
  const lastAssistantMessage = messages.filter((m) => m.role === "assistant").pop();

  const handleAgentSimulation = useCallback((sim: ParallelSimulationState) => {
    const items: TaskItem[] = [];
    if (sim.modelActive && sim.modelTask) {
      items.push({ id: "model", text: sim.modelTask, active: true });
    }
    sim.tasks.forEach((task, index) => {
      items.push({
        id: task.agentId,
        text: `${task.agentName}: ${task.task}`,
        active: !sim.modelActive && index === 0,
      });
    });
    setAgentLiveTasks(items.length > 0 ? items : null);
  }, []);

  useEffect(() => {
    if (!showAgentDashboard) {
      setAgentLiveTasks(null);
    }
  }, [showAgentDashboard]);

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

  const displayName = greetingDisplayName(user?.full_name, user?.email ?? "");
  const showWelcomeHero = !showAgentDashboard;

  return (
    <div className="flex h-screen w-full overflow-hidden relative font-sans">
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="sidebar-backdrop"
            initial={enterOrSkip(uiReady, { opacity: 0 })}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-background/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        uiReady={uiReady}
        activeHistoryId={activeHistoryId}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSelectHistory={handleSelectHistory}
        onDeleteHistory={handleDeleteHistory}
        onShareHistory={shareHistory}
        onNewChat={handleNewChat}
        agentModeActive={agentModeActive}
        onAgentsClick={handleAgentsNav}
      />

      <main className="relative flex flex-1 flex-col min-w-0 w-full h-screen overflow-hidden bg-background">
        <Header sidebarOpen={sidebarOpen} />

        <div className="relative flex-1 min-h-0">
          <AnimatePresence>
            {showWelcomeHero && (
              <motion.div
                key="welcome-hero"
                initial={enterOrSkip(uiReady, { opacity: 0, y: 12 })}
                animate={{
                  opacity: copycatMode ? 0.35 : 1,
                  y: 0,
                  scale: copycatMode ? 0.985 : 1,
                  filter: copycatMode ? "blur(6px)" : "blur(0px)",
                }}
                exit={{ opacity: 0, y: -8, scale: 0.99 }}
                transition={overlayFade}
                className={`${MAIN_STAGE} z-10`}
              >
                <div
                  className={`${MAIN_COLUMN} text-center ${
                    copycatMode ? "pointer-events-none" : "pointer-events-auto"
                  }`}
                >
                <h1 className="text-4xl sm:text-[56px] leading-[1.1] font-medium tracking-tight px-2">
                  <span className="text-on-surface-variant">Hello, </span>
                  <span className="bg-gradient-to-r from-[#4285F4] via-[#9B72CB] to-[#D96570] bg-clip-text text-transparent">
                    {displayName}
                  </span>
                </h1>
                {!hasMessages && (
                  <div className="mt-10 flex flex-wrap justify-center gap-2">
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
                )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {hasMessages && (
            <div className={`${MAIN_STAGE} z-0 md:hidden pointer-events-auto justify-start pt-6`}>
              <div className={`${MAIN_COLUMN} flex flex-col gap-4`}>
                <AiResponseCard
                  prompt={lastUserMessage?.content || ""}
                  response={lastAssistantMessage?.content || ""}
                  isStreaming={isStreaming}
                  thinkingSteps={thinkingSteps}
                  onEdit={handleEdit}
                  error={error}
                />
              </div>
            </div>
          )}

          <AnimatePresence>
            {showAgentDashboard && (
              <motion.div
                key="agent-mode-shell"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={overlayFade}
                className={`${MAIN_STAGE} z-20`}
              >
                <div className="w-full max-w-4xl mx-auto h-[min(480px,calc(100%-1rem))] pointer-events-auto">
                  <AgentDashboard
                    embedded
                    onClose={handleCloseAgentView}
                    onSimulationChange={handleAgentSimulation}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <LayoutGroup id="mode-switch">
            <AnimatePresence>
              {copycatMode && (
                <ComputerView
                  key="copycat-mode"
                  embedded
                  onExitCopycat={() => setCopycatMode(false)}
                />
              )}
            </AnimatePresence>

            <AnimatePresence mode="popLayout">
              {!copycatMode && (
                <div className={PROMPT_SLOT}>
                  <PromptBar
                    key="chat-mode-bar"
                    embedded
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
                    selectedTools={selectedTools}
                    onToggleTool={handleToggleTool}
                  />
                </div>
              )}
            </AnimatePresence>
          </LayoutGroup>
        </div>

        <motion.div
          className="hidden md:flex fixed top-20 right-6 bottom-6 w-[360px] flex-col gap-4 z-40 pointer-events-none"
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
              liveTasks={showAgentDashboard ? agentLiveTasks : null}
              agentMode={showAgentDashboard}
            />
          </div>
        </motion.div>

        <div className="md:hidden fixed bottom-28 left-0 right-0 z-20 flex justify-center px-4 pointer-events-none">
          <div className="w-full max-w-md pointer-events-auto">
            <TaskPanel
              tasksCollapsed={tasksCollapsed}
              setTasksCollapsed={setTasksCollapsed}
              uiReady={uiReady}
              liveTasks={showAgentDashboard ? agentLiveTasks : null}
              agentMode={showAgentDashboard}
            />
          </div>
        </div>

      </main>
    </div>
  );
}
