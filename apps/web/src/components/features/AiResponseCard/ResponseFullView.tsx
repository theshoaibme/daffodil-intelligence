import { useEffect } from "react";
import type { ChatMessage } from "@hooks";
import type { ThinkingStep } from "./ThinkingProcess";
import { ConversationThread } from "./ConversationThread";

interface ResponseFullViewProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  hasActiveWork?: boolean;
  error?: string | null;
  onClose?: () => void;
  onEditUserMessage?: (messageId: string, content: string) => void;
}

/** Center-column conversation (ChatGPT-style) — lives in the main stage, not a modal. */
export function ResponseFullView({
  messages,
  isStreaming = false,
  thinkingSteps = [],
  thinkingText = "",
  thinkingMs = null,
  hasActiveWork = false,
  error = null,
  onClose,
  onEditUserMessage,
}: ResponseFullViewProps) {
  useEffect(() => {
    if (!onClose) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="flex flex-col h-full min-h-0 w-full pointer-events-auto">
      <ConversationThread
        messages={messages}
        isStreaming={isStreaming}
        thinkingSteps={thinkingSteps}
        thinkingText={thinkingText}
        thinkingMs={thinkingMs}
        hasActiveWork={hasActiveWork}
        error={error}
        variant="center"
        showSidePanelFooter={Boolean(onClose)}
        onSidePanel={onClose}
        onEditUserMessage={onEditUserMessage}
      />
    </div>
  );
}
