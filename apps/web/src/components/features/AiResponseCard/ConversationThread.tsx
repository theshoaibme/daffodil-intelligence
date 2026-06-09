import { useEffect, useRef } from "react";
import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "@hooks";
import type { ThinkingStep } from "./ThinkingProcess";
import { ThinkingProcess } from "./ThinkingProcess";
import { ResponseContent } from "./ResponseContent";
import { parseResponseText } from "./responseParse";
import { ActionButtons } from "./ActionButtons";
import { UserMessageRow } from "./UserMessageRow";

export interface ConversationThreadProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  error?: string | null;
  variant?: "center" | "panel";
  onFullView?: () => void;
  onSidePanel?: () => void;
  showSidePanelFooter?: boolean;
  autoScroll?: boolean;
  onEditUserMessage?: (messageId: string, content: string) => void;
}

export function ConversationThread({
  messages,
  isStreaming = false,
  thinkingSteps = [],
  thinkingText = "",
  thinkingMs = null,
  error = null,
  variant = "center",
  onFullView,
  onSidePanel,
  showSidePanelFooter = false,
  autoScroll = true,
  onEditUserMessage,
}: ConversationThreadProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isPanel = variant === "panel";
  const lastAssistant = messages.filter((m) => m.role === "assistant").pop();
  const isLastAssistantStreaming =
    isStreaming && lastAssistant && (!lastAssistant.content.trim() || lastAssistant.isStreaming);

  useEffect(() => {
    if (!autoScroll || !scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [autoScroll, messages, isStreaming, thinkingText]);

  const showActions = (message: ChatMessage, isLast: boolean) => {
    if (message.role !== "assistant" || !message.content.trim()) return false;
    if (isLast && isStreaming) return false;
    return true;
  };

  return (
    <div className="flex flex-col h-full min-h-0 w-full">
      <div
        ref={scrollRef}
        className={`flex-1 min-h-0 overflow-y-auto no-scrollbar ${
          isPanel ? "px-2 py-2" : "px-1 sm:px-2 py-2 sm:py-4"
        }`}
      >
        <div
          className={`w-full mx-auto flex flex-col pb-4 ${
            isPanel ? "gap-4 max-w-full" : "gap-5 sm:gap-6 max-w-[48rem] pb-6"
          }`}
        >
          {messages.map((message, index) => {
            const isLast = index === messages.length - 1;
            const isUser = message.role === "user";

            if (isUser) {
              return (
                <UserMessageRow
                  key={message.id}
                  content={message.content}
                  isPanel={isPanel}
                  disabled={isStreaming}
                  onEdit={
                    onEditUserMessage
                      ? () => onEditUserMessage(message.id, message.content)
                      : undefined
                  }
                />
              );
            }

            const responseData = parseResponseText(message.content);
            const showThinking =
              isLast && isLastAssistantStreaming && !message.content.trim();
            const showStreaming = isLast && isStreaming && Boolean(message.content.trim());

            return (
              <div key={message.id} className="flex flex-col items-start w-full">
                <div className={`w-full text-left ${isPanel ? "px-0.5" : "px-1 sm:px-2 py-1"}`}>
                  {showThinking && (
                    <div className="mb-3">
                      <ThinkingProcess
                        isThinking
                        steps={thinkingSteps}
                        thinkingText={thinkingText}
                        thinkingMs={thinkingMs}
                        isExpanded
                        onToggleExpand={() => {}}
                      />
                    </div>
                  )}

                  {message.content.trim() ? (
                    <div className="min-h-[1.5rem] [&_.no-scrollbar]:max-h-none">
                      <ResponseContent
                        isThinking={false}
                        isStreaming={showStreaming}
                        data={responseData}
                        variant="chat"
                      />
                    </div>
                  ) : !showThinking ? (
                    <p className="text-sm text-on-surface-variant/70">No response yet.</p>
                  ) : null}
                </div>

                {showActions(message, isLast) && (
                  <ActionButtons
                    textToCopy={message.content}
                    embedded
                    showFullView={false}
                    showSidePanel={false}
                  />
                )}
              </div>
            );
          })}

          {error && (
            <div className="flex justify-start w-full">
              <div className="flex items-center gap-2 text-error text-sm px-1">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {isPanel && onFullView && (
        <footer className="shrink-0 pt-2 px-2">
          <ActionButtons
            textToCopy={lastAssistant?.content ?? ""}
            footer
            showCopyActions={false}
            showFullView
            onFullView={onFullView}
          />
        </footer>
      )}

      {showSidePanelFooter && onSidePanel && (
        <footer className="shrink-0 pt-2 px-2">
          <ActionButtons
            textToCopy={lastAssistant?.content ?? ""}
            footer
            showCopyActions={false}
            showFullView={false}
            showSidePanel
            onSidePanel={onSidePanel}
          />
        </footer>
      )}
    </div>
  );
}
