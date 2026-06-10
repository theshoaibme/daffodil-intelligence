/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import {

  AUTO_MODEL_ID,
  DEFAULT_AGENT_MODE,
  MOBILE_INPUT_WIDTH_CLASS,
  MOBILE_TASK_PANEL_SHELL_CLASS,
  MOBILE_TASK_PANEL_WIDTH_CLASS,
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
import { useChat, useChatContext, useIsLgUp, useLocalStorageState } from "@hooks";
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

const MAIN_STAGE_BASE =
  "absolute inset-0 flex px-3 sm:px-4 pb-[12.5rem] md:pb-[7rem] lg:pb-[8.5rem] pointer-events-none min-w-0";

/** Centered hero / overlay stages. */
const MAIN_STAGE_CENTER = `${MAIN_STAGE_BASE} items-center justify-center`;

/** Top-aligned conversation + agent visualize stack. */
const MAIN_STAGE_STACK = `${MAIN_STAGE_BASE} items-stretch justify-start pt-2 sm:pt-3 overflow-hidden`;

/** Mobile: task manager + input stacked flush. Desktop: input only in center column. */
const BOTTOM_DOCK =
  "fixed md:absolute bottom-0 md:bottom-4 lg:bottom-6 inset-x-0 z-30 flex flex-col gap-0 pointer-events-none px-3 sm:px-4 pb-4 md:pb-0";

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
  const isLgUp = useIsLgUp();
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
    if (!isLgUp) setSidebarOpen(false);
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
          paddingLeft: isLgUp
            ? sidebarOpen
              ? SIDEBAR_WIDTH_EXPANDED
              : SIDEBAR_WIDTH_COLLAPSED
            : 0,
        }}
        transition={sidebarWidthTransition}
      >
        <Header onOpenSidebar={() => setSidebarOpen(true)} />

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
                className={`${MAIN_STAGE_CENTER} z-10`}
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
              className={`${MAIN_STAGE_STACK} z-10`}
            >
              <div
                className={`w-full mx-auto min-w-0 h-full min-h-0 max-h-full pointer-events-auto px-1 ${
                  showSplitAgentAndChat
                    ? "max-w-4xl grid grid-rows-[minmax(280px,50%)_minmax(0,1fr)] gap-2"
                    : "max-w-3xl flex flex-col justify-center"
                }`}
              >
                {showSplitAgentAndChat && (
                  <div className="min-h-0 w-full self-start overflow-hidden rounded-2xl border border-outline-variant/30 shadow-sm">
                    <AgentDashboard embedded onClose={handleCloseAgentView} />
                  </div>
                )}
                <div className="min-h-0 overflow-hidden">
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
            <div className={`${MAIN_STAGE_STACK} z-0 md:hidden pointer-events-auto pt-4 sm:pt-6 overflow-y-auto no-scrollbar`}>
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
                className={`${MAIN_STAGE_STACK} z-20`}
              >
                <div className="w-full max-w-4xl mx-auto h-[min(560px,calc(100%-1rem))] min-h-[300px] sm:min-h-[360px] pointer-events-auto px-1 sm:px-0 self-start pt-2">
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
                <div className={`${BOTTOM_DOCK} max-md:items-center`}>
                  <div className="md:contents flex w-full flex-col gap-0 max-md:items-center">
                    <div
                      className={`md:hidden pointer-events-auto ${MOBILE_TASK_PANEL_WIDTH_CLASS} ${MOBILE_TASK_PANEL_SHELL_CLASS}`}
                    >
                      <TaskPanel
                        inset
                        tasksCollapsed={tasksCollapsed}
                        setTasksCollapsed={setTasksCollapsed}
                        uiReady={uiReady}
                        liveTasks={taskPanelLiveTasks}
                        agentMode={taskPanelLive}
                      />
                    </div>
                    <div className="w-full flex justify-center pointer-events-auto max-md:-mt-px">
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
                        shellClassName={MOBILE_INPUT_WIDTH_CLASS}
                      />
                    </div>
                  </div>
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

      </motion.main>
    </div>
  );
}
