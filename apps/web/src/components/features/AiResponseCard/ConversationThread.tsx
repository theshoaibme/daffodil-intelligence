import { useEffect, useRef } from "react";
import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "@hooks";
import type { ThinkingStep } from "./ThinkingProcess";
import { ThinkingProcess } from "./ThinkingProcess";
import { ResponseContent } from "./ResponseContent";
import { parseResponseText } from "./responseParse";
import { ActionButtons } from "./ActionButtons";
import { UserMessageRow } from "./UserMessageRow";
import { StructuredBlockRenderer } from "@components/ui/blocks";
import { coerceUiBlocks } from "@lib/uiBlocks/coerce";
import { normalizeUiBlocks } from "@lib/uiBlocks/normalize";
import { sanitizeAssistantContent } from "@lib/uiBlocks/sanitizeContent";
import type { UiBlock } from "@lib/uiBlocks/types";
import { hasThinkingContent } from "@lib/thinkingText";

export interface ConversationThreadProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  hasActiveWork?: boolean;
  error?: string | null;
  variant?: "center" | "panel";
  onFullView?: () => void;
  onSidePanel?: () => void;
  showSidePanelFooter?: boolean;
  autoScroll?: boolean;
  onEditUserMessage?: (messageId: string, content: string) => void;
}

function messageThinkingText(
  message: ChatMessage,
  isLast: boolean,
  liveThinking: string
): string {
  const stored = String(message.metadata?.thinking_text ?? "");
  if (isLast && liveThinking) return liveThinking;
  return stored;
}

export function ConversationThread({
  messages,
  isStreaming = false,
  thinkingText = "",
  thinkingMs = null,
  hasActiveWork = false,
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

  useEffect(() => {
    if (!autoScroll || !scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [autoScroll, messages, isStreaming, thinkingText, hasActiveWork]);

  const showActions = (message: ChatMessage, isLast: boolean) => {
    const blocks = coerceUiBlocks((message.metadata?.ui_blocks as UiBlock[] | undefined) ?? []);
    const display = sanitizeAssistantContent(message.content, blocks);
    const hasUi = blocks.length > 0;
    if (message.role !== "assistant" || (!display.trim() && !hasUi)) return false;
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
                  voiceMessage={Boolean(message.metadata?.voice_message)}
                  voiceDurationMs={
                    typeof message.metadata?.voice_duration_ms === "number"
                      ? message.metadata.voice_duration_ms
                      : undefined
                  }
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

            const uiBlocks = normalizeUiBlocks(
              coerceUiBlocks((message.metadata?.ui_blocks as UiBlock[] | undefined) ?? [])
            );
            const displayContent = sanitizeAssistantContent(message.content, uiBlocks);
            const responseData = parseResponseText(displayContent);
            const hasBlocks = uiBlocks.length > 0;
            const rawThinking = messageThinkingText(message, isLast, thinkingText);
            const showThinking =
              hasThinkingContent(rawThinking) || (isLast && isStreaming);
            const showStreaming = isLast && isStreaming && Boolean(displayContent.trim());

            return (
              <div key={message.id} className="flex flex-col items-start w-full">
                <div className={`w-full text-left ${isPanel ? "px-0.5" : "px-1 sm:px-2 py-1"}`}>
                  {showThinking && (
                    <div className="mb-2">
                      <ThinkingProcess
                        key={`thinking-${message.id}`}
                        isThinking={isLast && isStreaming}
                        thinkingText={rawThinking}
                        thinkingMs={
                          isLast
                            ? thinkingMs
                            : (message.metadata?.thinking_ms as number | null)
                        }
                      />
                    </div>
                  )}

                  {hasBlocks ? (
                    <div className="mb-2">
                      <StructuredBlockRenderer blocks={uiBlocks} />
                    </div>
                  ) : null}

                  {displayContent.trim() ? (
                    <div
                      className={`min-h-[1.5rem] [&_.no-scrollbar]:max-h-none ${
                        hasBlocks ? "text-sm text-on-surface-variant" : ""
                      }`}
                    >
                      <ResponseContent
                        isThinking={false}
                        isStreaming={showStreaming}
                        data={responseData}
                        variant="chat"
                      />
                    </div>
                  ) : !showThinking && !hasBlocks ? (
                    <p className="text-sm text-on-surface-variant/70">No response yet.</p>
                  ) : null}
                </div>

                {showActions(message, isLast) && (
                  <ActionButtons
                    textToCopy={displayContent || message.content}
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
