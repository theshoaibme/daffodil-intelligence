/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import {

  AUTO_MODEL_ID,
  DEFAULT_AGENT_MODE,
  enterOrSkip,
  getHistoryEntry,
  hubApi,
  modeSpring,
  normalizeAgentMode,
  overlayFade,
  readLocalMcpServers,
  ROUTES,
  sidebarWidthTransition,
  hasActivePanelWork,
  tasksToPanelItems,
  type AgentMode,
} from "@lib";
import { useChat, useChatContext, useLocalStorageState } from "@hooks";
import {
  ChatHistoryProvider,
  UiAnimationProvider,
  useAuth,
  useChatHistory,
  useUiAnimationReady,
} from "@context";
import { SuggestionChip } from "@ui";
import { Sidebar, Header, SIDEBAR_WIDTH_COLLAPSED, SIDEBAR_WIDTH_EXPANDED } from "@layout";
import {
  PromptBar,
  TaskPanel,
  AiResponseCard,
  ResponseFullView,
  AgentDashboard,
  ComputerView,
} from "@features";
import type { TaskItem } from "@features/TaskPanel/TaskPanel";

import { Routes, Route, Navigate, useSearchParams } from "react-router-dom";
import {
  ModelManagementPage,
  LiveVoicePage,
  AuthTelegramPage,
  LoginPage,
  RegisterPage,
  GuidancePage,
  SkillsPage,
  AgentHubPage,
  GoogleCallbackPage,
  AccountPage,
  LandingPage,
  TermsPage,
  PrivacyPage,
  CopycatAuthPage,
} from "@pages";
import { ProtectedRoute } from "@auth";

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
        <Route path={ROUTES.agents} element={<Navigate to={ROUTES.agentHub} replace />} />
        <Route path={ROUTES.skills} element={<SkillsPage />} />
        <Route path={ROUTES.agentHub} element={<AgentHubPage />} />
        <Route path={ROUTES.computer} element={<ComputerView />} />
        <Route path={ROUTES.guidance} element={<GuidancePage />} />
        <Route path={ROUTES.account} element={<AccountPage />} />
        <Route path={ROUTES.copycat} element={<CopycatAuthPage />} />
      </Route>
    </Routes>
  );
}

const DASHBOARD_STORAGE_KEYS = {
  sidebarOpen: "di-dashboard-sidebar-open",
  tasksCollapsed: "di-dashboard-tasks-collapsed",
  promptDraft: "di-dashboard-prompt-draft",
  agentMode: "di-dashboard-agent-mode",
} as const;

/** Horizontal column width — shared by welcome hero and prompt bar. */
const MAIN_COLUMN = "w-full max-w-xl mx-auto min-w-0";

/** Fills center column below header; pb reserves prompt bar. */
const MAIN_STAGE =
  "absolute inset-0 flex items-center justify-center px-3 sm:px-4 pb-[7rem] sm:pb-[8.5rem] pointer-events-none min-w-0";

/** Prompt bar slot — pinned to bottom of center column. */
const PROMPT_SLOT =
  "absolute bottom-4 sm:bottom-6 left-1/2 -translate-x-1/2 w-full max-w-xl px-3 sm:px-4 z-30 pointer-events-none min-w-0";

/** Right rail: chat response + task panel (md+). */
const RIGHT_RAIL =
  "hidden md:flex flex-col self-stretch min-h-0 min-w-0 h-full gap-3 lg:gap-4 pr-3 lg:pr-5 xl:pr-6 pb-4 lg:pb-6 overflow-hidden pointer-events-none";

function greetingDisplayName(fullName: string | null | undefined, email: string): string {
  if (fullName?.trim()) return fullName.trim();
  const local = email.split("@")[0]?.trim();
  return local || "there";
}

function ChatDashboard() {
  const uiReady = useUiAnimationReady();
  const { user } = useAuth();
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
  const [selectedAgentMode, setSelectedAgentMode] = useLocalStorageState<AgentMode>(
    DASHBOARD_STORAGE_KEYS.agentMode,
    DEFAULT_AGENT_MODE
  );
  const [prompt, setPrompt] = useLocalStorageState(DASHBOARD_STORAGE_KEYS.promptDraft, "");
  const [selectedModelId] = useLocalStorageState(
    "di-dashboard-selected-model",
    AUTO_MODEL_ID
  );
  const [agentMenuOpen, setAgentMenuOpen] = useState(false);
  const [tasksCollapsed, setTasksCollapsed] = useLocalStorageState(
    DASHBOARD_STORAGE_KEYS.tasksCollapsed,
    false
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const handledAgentsParam = useRef(false);
  const lastUrlChatRef = useRef<string | null>(searchParams.get("chat"));
  const [agentSimulationOpen, setAgentSimulationOpen] = useState(false);
  const [suggestionSkills, setSuggestionSkills] = useState<{ id: string; name: string }[]>([]);
  const [preferSidePanel, setPreferSidePanel] = useState(false);

  const agentModeActive = selectedAgentMode === "Agent" && !copycatMode;

  const handleSelectAgentMode = (mode: AgentMode) => {
    setSelectedAgentMode(mode);
    if (mode !== "Agent") {
      setAgentSimulationOpen(false);
    } else {
      setAgentSimulationOpen(true);
    }
  };

  const handleCloseAgentView = () => {
    setAgentSimulationOpen(false);
  };

  const initialSession = activeHistoryId ? getHistoryEntry(activeHistoryId) : null;
  const {
    chatId,
    messages,
    isStreaming,
    thinkingSteps,
    agentTasks,
    thinkingText,
    thinkingMs,
    error,
    lastContext,
    send,
    loadSession,
    truncateFromMessage,
  } = useChat({
    initialChatId: initialSession?.chatId ?? null,
    initialMessages: initialSession?.messages ?? [],
  });

  const fetchedContext = useChatContext(chatId, messages, prompt, selectedModelId);
  const chatContext = isStreaming && lastContext ? lastContext : fetchedContext;

  useEffect(() => {
    try {
      const current = localStorage.getItem(DASHBOARD_STORAGE_KEYS.agentMode);
      const legacy = localStorage.getItem("di-dashboard-selected-tools");
      if (current === null && legacy) {
        setSelectedAgentMode(normalizeAgentMode(JSON.parse(legacy)));
      }
    } catch {
      // ignore invalid legacy storage
    }
  }, [setSelectedAgentMode]);

  useEffect(() => {
    hubApi
      .listSkills({ limit: 3 })
      .then((data) => {
        setSuggestionSkills(
          data.skills.slice(0, 3).map((skill) => ({ id: skill.id, name: skill.name }))
        );
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (isStreaming) return;
    syncActiveSession(chatId, messages);
  }, [chatId, messages, isStreaming, syncActiveSession]);

  const flushCurrentSession = useCallback(() => {
    if (!isStreaming) {
      syncActiveSession(chatId, messages);
    }
  }, [isStreaming, syncActiveSession, chatId, messages]);

  // Load session when ?chat= in the URL changes (share links, browser back/forward).
  useEffect(() => {
    const chatParam = searchParams.get("chat");
    if (!chatParam) {
      lastUrlChatRef.current = null;
      return;
    }
    if (lastUrlChatRef.current === chatParam) return;
    lastUrlChatRef.current = chatParam;

    const session = selectHistory(chatParam);
    loadSession(session.chatId, session.messages);
  }, [searchParams, selectHistory, loadSession]);

  // Keep ?chat= in sync with the active sidebar session (no searchParams in deps — avoids loops).
  useEffect(() => {
    const chatParam = searchParams.get("chat");
    if (activeHistoryId) {
      if (chatParam !== activeHistoryId) {
        setSearchParams(
          (prev) => {
            const next = new URLSearchParams(prev);
            next.set("chat", activeHistoryId);
            return next;
          },
          { replace: true }
        );
      }
      return;
    }
    if (chatParam) {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.delete("chat");
          return next;
        },
        { replace: true }
      );
    }
  }, [activeHistoryId, setSearchParams]);

  useEffect(() => {
    if (handledAgentsParam.current) return;
    if (searchParams.get("agents") !== "1") return;

    handledAgentsParam.current = true;
    setSelectedAgentMode("Agent");
    setAgentSimulationOpen(true);
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete("agents");
        return next;
      },
      { replace: true }
    );
  }, [searchParams, setSearchParams, setSelectedAgentMode]);

  const handleSelectHistory = (id: string) => {
    if (id === activeHistoryId) return;
    flushCurrentSession();
    lastUrlChatRef.current = id;
    const session = selectHistory(id);
    loadSession(session.chatId, session.messages);
    setPrompt("");
  };

  const handleNewChat = () => {
    flushCurrentSession();
    const session = startNewChat();
    lastUrlChatRef.current = session.sessionId;
    loadSession(session.chatId, session.messages);
    setPrompt("");
    setAgentSimulationOpen(false);
    setPreferSidePanel(false);
  };

  const handleDeleteHistory = (id: string) => {
    const wasActive = activeHistoryId === id;
    if (wasActive) {
      flushCurrentSession();
    }
    deleteHistory(id);
    if (wasActive) {
      loadSession(null, []);
      setPrompt("");
    }
  };

  const hasMessages = messages.length > 0;
  const showResponsePanel = hasMessages && !copycatMode;

  useEffect(() => {
    if (agentModeActive && isStreaming) {
      setAgentSimulationOpen(true);
    }
  }, [agentModeActive, isStreaming]);

  const showAgentDashboard = agentModeActive && agentSimulationOpen;
  const showMainConversation = showResponsePanel && !preferSidePanel;
  /** Agent + chat split in center — stays mounted after stream ends (no layout swap). */
  const showSplitAgentAndChat = showAgentDashboard && showMainConversation;
  /** Full agent canvas when side panel chat or no messages yet. */
  const showAgentGraph =
    showAgentDashboard && (preferSidePanel || !showResponsePanel);

  const taskPanelLiveTasks = useMemo<TaskItem[] | null>(() => {
    const items = tasksToPanelItems(agentTasks);
    return items.length > 0 ? items : null;
  }, [agentTasks]);

  const hasActiveWork = useMemo(
    () => isStreaming && hasActivePanelWork(agentTasks),
    [agentTasks, isStreaming]
  );

  const taskPanelLive = taskPanelLiveTasks !== null;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [prompt]);

  const sendPrompt = async (text: string, modelId?: string) => {
    if (!text.trim()) return;

    if (!activeHistoryId) {
      const session = startNewChat();
      lastUrlChatRef.current = session.sessionId;
      loadSession(session.chatId, session.messages);
    }

    const mcpServers = readLocalMcpServers();
    const selectedTools = new Set<string>([selectedAgentMode]);
    const routineLike =
      /\b(class routine|class schedule|my routine|daily schedule|section routine)\b/i.test(
        text
      );
    if (
      selectedAgentMode === "MCP" ||
      selectedAgentMode === "Agent" ||
      selectedAgentMode === "Planning" ||
      routineLike
    ) {
      selectedTools.add("MCP");
    }

    const chatMetadata: Record<string, unknown> = {
      selected_tools: [...selectedTools],
      channel: "chat",
    };
    if (user?.department) {
      chatMetadata.department = user.department;
    }
    if (user?.student_id) {
      chatMetadata.student_id = user.student_id;
    }
    if (mcpServers.length > 0) {
      chatMetadata.mcp_servers = mcpServers.map((server) => ({
        name: server.name,
        command: server.command,
      }));
    }

    setPrompt("");
    await send(text, modelId, chatMetadata);
  };

  const handleSend = (modelId: string) => {
    sendPrompt(prompt, modelId);
  };

  const handleEditUserMessage = (messageId: string, content: string) => {
    truncateFromMessage(messageId);
    setPrompt(content);
    setTimeout(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(content.length, content.length);
    }, 50);
  };

  const displayName = greetingDisplayName(user?.full_name, user?.email ?? "");
  const showSideResponse = showResponsePanel && preferSidePanel;
  const showWelcomeHero = !showAgentGraph && !showMainConversation;

  const toggleAgentVisualize = () => {
    setAgentSimulationOpen((open) => !open);
  };

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
            className="fixed inset-0 bg-background/50 z-40 lg:hidden"
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
      />

      <motion.main
        className="relative flex flex-1 flex-col min-w-0 w-full h-screen overflow-hidden bg-background"
        initial={false}
        animate={{
          paddingLeft: sidebarOpen ? SIDEBAR_WIDTH_EXPANDED : SIDEBAR_WIDTH_COLLAPSED,
        }}
        transition={sidebarWidthTransition}
      >
        <Header />

        <div
          className={`relative flex-1 min-h-0 min-w-0 grid grid-cols-1 ${
            copycatMode
              ? ""
              : "md:grid-cols-[minmax(0,1fr)_minmax(240px,min(360px,30vw))] lg:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]"
          }`}
        >
        <div className="relative min-h-0 min-w-0">
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
                <h1 className="text-3xl sm:text-4xl lg:text-[56px] leading-[1.1] font-medium tracking-tight px-2">
                  <span className="text-on-surface-variant">Hello, </span>
                  <span className="bg-gradient-to-r from-[#4285F4] via-[#9B72CB] to-[#D96570] bg-clip-text text-transparent">
                    {displayName}
                  </span>
                </h1>
                {!hasMessages && suggestionSkills.length > 0 && (
                  <div className="mt-10 flex flex-wrap justify-center gap-2">
                    {suggestionSkills.map((skill) => (
                      <SuggestionChip
                        key={skill.id}
                        text={skill.name}
                        onClick={() => sendPrompt(skill.name)}
                      />
                    ))}
                  </div>
                )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {showMainConversation && (
            <motion.div
              key="main-conversation"
              initial={false}
              className={`${MAIN_STAGE} z-10 items-stretch justify-start pt-2 sm:pt-3 overflow-hidden`}
            >
              <div
                className={`w-full mx-auto min-w-0 h-full min-h-0 max-h-full flex flex-col pointer-events-auto px-1 ${
                  showSplitAgentAndChat ? "max-w-4xl gap-2" : "max-w-3xl justify-center"
                }`}
              >
                {showSplitAgentAndChat && (
                  <div className="flex-[0_0_38%] min-h-[180px] sm:min-h-[220px] max-h-[42%] shrink-0">
                    <AgentDashboard embedded onClose={handleCloseAgentView} />
                  </div>
                )}
                <div className={showSplitAgentAndChat ? "flex-1 min-h-0 overflow-hidden" : "min-h-0 flex-1"}>
                  <ResponseFullView
                    messages={messages}
                    isStreaming={isStreaming}
                    thinkingSteps={thinkingSteps}
                    thinkingText={thinkingText}
                    thinkingMs={thinkingMs}
                    hasActiveWork={hasActiveWork}
                    error={error}
                    onClose={() => setPreferSidePanel(true)}
                    onEditUserMessage={handleEditUserMessage}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {showSideResponse && (
            <div className={`${MAIN_STAGE} z-0 md:hidden pointer-events-auto justify-start pt-4 sm:pt-6 overflow-y-auto no-scrollbar`}>
              <div className={`${MAIN_COLUMN} flex flex-col gap-4 min-h-0 max-h-full`}>
                <AiResponseCard
                  messages={messages}
                  isStreaming={isStreaming}
                  thinkingSteps={thinkingSteps}
                  thinkingText={thinkingText}
                  thinkingMs={thinkingMs}
                  hasActiveWork={hasActiveWork}
                  error={error}
                  onFullView={() => setPreferSidePanel(false)}
                  onEditUserMessage={handleEditUserMessage}
                />
              </div>
            </div>
          )}

          <AnimatePresence>
            {showAgentGraph && !showSplitAgentAndChat && (
              <motion.div
                key="agent-mode-shell"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={overlayFade}
                className={`${MAIN_STAGE} z-20`}
              >
                <div className="w-full max-w-4xl mx-auto h-[min(480px,calc(100%-0.5rem))] min-h-[220px] sm:min-h-[280px] pointer-events-auto px-1 sm:px-0">
                  <AgentDashboard embedded onClose={handleCloseAgentView} />
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
                    agentMenuOpen={agentMenuOpen}
                    setAgentMenuOpen={setAgentMenuOpen}
                    textareaRef={textareaRef}
                    isStreaming={isStreaming}
                    context={chatContext}
                    onCopycatMode={() => setCopycatMode(true)}
                    copycatActive={copycatMode}
                    selectedAgentMode={selectedAgentMode}
                    onSelectAgentMode={handleSelectAgentMode}
                    agentVisualizeOpen={agentSimulationOpen}
                    onToggleAgentVisualize={toggleAgentVisualize}
                  />
                </div>
              )}
            </AnimatePresence>
          </LayoutGroup>
        </div>

        {!copycatMode && (
          <motion.div
            className={RIGHT_RAIL}
            initial={false}
            animate={{ opacity: 1, x: 0 }}
            transition={modeSpring}
          >
            <AnimatePresence>
              {showSideResponse && (
                <motion.div
                  initial={enterOrSkip(uiReady, { opacity: 0, y: -20, scale: 0.95 })}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -20, scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                  className="pointer-events-auto flex-1 min-h-0 flex flex-col overflow-hidden"
                >
                  <AiResponseCard
                    messages={messages}
                    isStreaming={isStreaming}
                    thinkingSteps={thinkingSteps}
                    thinkingText={thinkingText}
                    thinkingMs={thinkingMs}
                    hasActiveWork={hasActiveWork}
                    error={error}
                    fillHeight
                    onFullView={() => setPreferSidePanel(false)}
                    onEditUserMessage={handleEditUserMessage}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="pointer-events-auto mt-auto w-full min-w-0 shrink-0">
              <TaskPanel
                tasksCollapsed={tasksCollapsed}
                setTasksCollapsed={setTasksCollapsed}
                uiReady={uiReady}
                liveTasks={taskPanelLiveTasks}
                agentMode={taskPanelLive}
              />
            </div>
          </motion.div>
        )}
        </div>

        <div className="md:hidden fixed bottom-[7.25rem] sm:bottom-28 left-0 right-0 z-20 flex justify-center px-3 sm:px-4 pointer-events-none">
          <div className="w-full max-w-md min-w-0 pointer-events-auto">
            <TaskPanel
              tasksCollapsed={tasksCollapsed}
              setTasksCollapsed={setTasksCollapsed}
              uiReady={uiReady}
              liveTasks={taskPanelLiveTasks}
              agentMode={taskPanelLive}
            />
          </div>
        </div>

      </motion.main>
    </div>
  );
}
