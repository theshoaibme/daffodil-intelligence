import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "@hooks";
import type { ThinkingStep } from "./ThinkingProcess";
import { ConversationThread } from "./ConversationThread";

interface AiResponseCardProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  hasActiveWork?: boolean;
  error?: string | null;
  fillHeight?: boolean;
  onFullView?: () => void;
  onEditUserMessage?: (messageId: string, content: string) => void;
}

export function AiResponseCard({
  messages,
  isStreaming = false,
  thinkingSteps = [],
  thinkingText = "",
  thinkingMs = null,
  hasActiveWork = false,
  error,
  fillHeight = false,
  onFullView,
  onEditUserMessage,
}: AiResponseCardProps) {
  const hasMessages = messages.length > 0;

  return (
    <div
      className={`w-full glass-gradient-panel border border-outline-variant/40 rounded-[28px] shadow-md text-left relative overflow-hidden flex flex-col min-w-0 select-text ${
        fillHeight
          ? "h-full min-h-[200px] max-h-full p-3 sm:p-4"
          : "max-w-md h-[min(360px,50dvh)] sm:h-[360px] p-3 sm:p-4"
      }`}
      id="ai-response-card"
    >
      {!hasMessages && error ? (
        <div className="flex items-center gap-2 text-error p-2">
          <AlertCircle size={18} />
          <span className="text-sm">{error}</span>
        </div>
      ) : (
        <ConversationThread
          messages={messages}
          isStreaming={isStreaming}
          thinkingSteps={thinkingSteps}
          thinkingText={thinkingText}
          thinkingMs={thinkingMs}
          hasActiveWork={hasActiveWork}
          error={error}
          variant="panel"
          onFullView={onFullView}
          onEditUserMessage={onEditUserMessage}
        />
      )}
    </div>
  );
}
