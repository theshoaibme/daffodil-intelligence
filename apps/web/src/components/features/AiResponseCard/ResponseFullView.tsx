import { useEffect, useRef } from "react";
import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "@hooks";
import type { ThinkingStep } from "./ThinkingProcess";
import { ThinkingProcess } from "./ThinkingProcess";
import { ResponseContent } from "./ResponseContent";
import { parseResponseText } from "./responseParse";
import { ActionButtons } from "./ActionButtons";

interface ResponseFullViewProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  error?: string | null;
  onClose?: () => void;
}

/** Center-column conversation (ChatGPT-style) — lives in the main stage, not a modal. */
export function ResponseFullView({
  messages,
  isStreaming = false,
  thinkingSteps = [],
  thinkingText = "",
  thinkingMs = null,
  error = null,
  onClose,
}: ResponseFullViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastAssistant = messages.filter((m) => m.role === "assistant").pop();
  const isLastAssistantStreaming =
    isStreaming && lastAssistant && (!lastAssistant.content.trim() || lastAssistant.isStreaming);

  useEffect(() => {
    if (!onClose) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isStreaming, thinkingText]);

  const showFooter =
    onClose || (lastAssistant?.content && !isStreaming && !error);

  return (
    <div className="flex flex-col h-full min-h-0 w-full pointer-events-auto">
      <div
        ref={scrollRef}
        className="flex-1 min-h-0 overflow-y-auto no-scrollbar px-1 sm:px-2 py-2 sm:py-4"
      >
        <div className="w-full max-w-[48rem] mx-auto flex flex-col gap-5 sm:gap-6 pb-6">
          {messages.map((message, index) => {
            const isLast = index === messages.length - 1;
            const isUser = message.role === "user";

            if (isUser) {
              return (
                <div key={message.id} className="flex justify-end w-full">
                  <div className="max-w-[88%] sm:max-w-[78%] rounded-3xl chat-bubble-user px-3 py-2 sm:px-3.5 sm:py-2.5">
                    <p className="text-sm text-on-surface whitespace-pre-wrap break-words leading-relaxed">
                      {message.content}
                    </p>
                  </div>
                </div>
              );
            }

            const responseData = parseResponseText(message.content);
            const showThinking =
              isLast && isLastAssistantStreaming && !message.content.trim();
            const showStreaming = isLast && isStreaming && Boolean(message.content.trim());

            return (
              <div key={message.id} className="flex justify-start w-full">
                <div className="w-full max-w-[42rem] text-left px-1 sm:px-2 py-1">
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
                    <div className="min-h-[1.5rem]">
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
              </div>
            );
          })}

          {error && (
            <div className="flex justify-center w-full">
              <div className="w-full max-w-[42rem] flex items-center gap-2 text-error text-sm">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {showFooter && (
        <footer className="shrink-0 pt-3 mt-1">
          <div className="w-full max-w-[48rem] mx-auto">
            <ActionButtons
              textToCopy={lastAssistant?.content ?? ""}
              embedded
              showFullView={false}
              showSidePanel={Boolean(onClose)}
              onSidePanel={onClose}
            />
          </div>
        </footer>
      )}
    </div>
  );
}
