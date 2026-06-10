import React, { useState } from "react";
import { motion } from "framer-motion";
import { AgentSelector } from "./AgentSelector";
import { McpConfigureDialog } from "./McpConfigureDialog";
import { ModelSelector } from "./ModelSelector";
import { ContextUseRing } from "./ContextUseRing";
import { FileAttachmentButton, MicButton, SendButton, StopButton } from "./ActionButtons";
import {
  AGENT_MODE_PLACEHOLDERS,
  AUTO_MODEL_ID,
  BOTTOM_BAR_LAYOUT_ID,
  enterOrSkip,
  modeSpring,
  type AgentMode,
  type ChatContextUsage,
} from "@lib";
import { useLocalStorageState } from "@hooks";
import { useMcpStatus } from "@hooks";

interface PromptBarProps {
  prompt: string;
  setPrompt: (val: string) => void;
  isSent?: boolean;
  handleSend: (modelId: string) => void;
  agentMenuOpen: boolean;
  setAgentMenuOpen: (open: boolean) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  isStreaming?: boolean;
  context?: ChatContextUsage;
  onCopycatMode?: () => void;
  copycatActive?: boolean;
  uiReady?: boolean;
  selectedAgentMode: AgentMode;
  onSelectAgentMode: (mode: AgentMode) => void;
  /** When true, omit viewport-fixed wrapper — parent positions the bar in the main column. */
  embedded?: boolean;
}

export function PromptBar({
  prompt,
  setPrompt,
  handleSend,
  agentMenuOpen,
  setAgentMenuOpen,
  textareaRef,
  isStreaming = false,
  context,
  onCopycatMode,
  copycatActive = false,
  uiReady = true,
  selectedAgentMode,
  onSelectAgentMode,
  embedded = false,
}: PromptBarProps) {
  const [selectedModelId, setSelectedModelId] = useLocalStorageState(
    "di-dashboard-selected-model",
    AUTO_MODEL_ID
  );

  const submit = () => handleSend(selectedModelId);
  const hasText = Boolean(prompt.trim());
  const showSend = hasText && !isStreaming;
  const showMic = !hasText && !isStreaming;
  const showStop = isStreaming;

  const [mcpDialogOpen, setMcpDialogOpen] = useState(false);
  const {
    status: mcpStatus,
    detail: mcpDetail,
    loading: mcpLoading,
    syncing: mcpSyncing,
    localServers,
    isConfigured: mcpConfigured,
    updateLocalServers,
    refetch: refetchMcpStatus,
    validateServer,
    testServer,
    testSelf,
  } = useMcpStatus();

  const promptBarInner = (
    <>
      <textarea
        ref={textareaRef}
        rows={1}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (hasText && !isStreaming) {
              submit();
            }
          }
        }}
        placeholder={AGENT_MODE_PLACEHOLDERS[selectedAgentMode]}
        className="w-full bg-transparent border-none outline-none resize-none text-sm text-on-surface placeholder-on-surface-variant focus:ring-0 px-1.5 py-1 leading-relaxed max-h-[200px]"
      />

      <div className="flex items-center justify-between px-0.5">
        <div className="flex items-center gap-1">
          <AgentSelector
            isOpen={agentMenuOpen}
            setIsOpen={setAgentMenuOpen}
            selectedMode={selectedAgentMode}
            onSelectMode={onSelectAgentMode}
            onCopycatMode={onCopycatMode}
            copycatActive={copycatActive}
            mcpConfigured={mcpConfigured}
            onConfigureMcp={() => setMcpDialogOpen(true)}
          />
          <ModelSelector selectedModelId={selectedModelId} onChange={setSelectedModelId} />
        </div>

        <div className="flex items-center gap-2.5">
          {context && <ContextUseRing context={context} />}
          <FileAttachmentButton />
          {showStop && <StopButton />}
          {showSend && <SendButton onClick={submit} />}
          {showMic && <MicButton />}
        </div>
      </div>
    </>
  );

  return (
    <>
      <McpConfigureDialog
        open={mcpDialogOpen}
        onClose={() => setMcpDialogOpen(false)}
        status={mcpStatus}
        detail={mcpDetail}
        localServers={localServers}
        onLocalServersChange={updateLocalServers}
        onRefreshStatus={refetchMcpStatus}
        loading={mcpLoading}
        syncing={mcpSyncing}
        onValidateServer={validateServer}
        onTestServer={testServer}
        onTestSelf={testSelf}
      />
      {embedded ? (
        <motion.div
          layoutId={BOTTOM_BAR_LAYOUT_ID}
          initial={enterOrSkip(uiReady, { opacity: 0, y: 14, scale: 0.96 })}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.94 }}
          transition={modeSpring}
          className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 flex flex-col gap-1 rounded-3xl px-2.5 py-2 relative shadow-md pointer-events-auto"
        >
          {promptBarInner}
        </motion.div>
      ) : (
        <div className="fixed bottom-6 left-0 right-0 z-30 flex justify-center w-full px-4 pointer-events-none">
          <motion.div
            layoutId={BOTTOM_BAR_LAYOUT_ID}
            initial={enterOrSkip(uiReady, { opacity: 0, y: 14, scale: 0.96 })}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.94 }}
            transition={modeSpring}
            className="w-full max-w-xl glass-gradient-panel border border-outline-variant/40 flex flex-col gap-1 rounded-3xl px-2.5 py-2 relative shadow-md pointer-events-auto"
          >
            {promptBarInner}
          </motion.div>
        </div>
      )}
    </>
  );
}
