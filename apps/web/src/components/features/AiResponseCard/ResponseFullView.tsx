import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Minimize2, X } from "lucide-react";
import type { ChatMessage } from "@hooks";
import type { ThinkingStep } from "./ThinkingProcess";
import { ThinkingProcess } from "./ThinkingProcess";
import { ResponseContent } from "./ResponseContent";
import { parseResponseText } from "./responseParse";
import { ActionButtons } from "./ActionButtons";
import { overlayFade } from "@lib";

interface ResponseFullViewProps {
  open: boolean;
  onClose: () => void;
  messages: ChatMessage[];
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  error?: string | null;
}

export function ResponseFullView({
  open,
  onClose,
  messages,
  isStreaming = false,
  thinkingSteps = [],
  thinkingText = "",
  thinkingMs = null,
  error = null,
}: ResponseFullViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastAssistant = messages.filter((m) => m.role === "assistant").pop();
  const lastUser = messages.filter((m) => m.role === "user").pop();
  const isLastAssistantStreaming =
    isStreaming && lastAssistant && (!lastAssistant.content.trim() || lastAssistant.isStreaming);

  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open || !scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [open, messages, isStreaming, thinkingText]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={overlayFade}
          className="fixed inset-0 z-[55] flex flex-col bg-background/92 backdrop-blur-md"
          role="dialog"
          aria-modal="true"
          aria-label="Full conversation view"
        >
          <header className="flex items-center justify-between gap-3 px-4 sm:px-6 py-3 border-b border-outline-variant/20 shrink-0">
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-on-surface">Conversation</h2>
              <p className="text-xs text-on-surface-variant mt-0.5">
                {messages.length} message{messages.length === 1 ? "" : "s"}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-on-surface-variant border border-outline-variant/30 hover:bg-surface-container-high transition-colors cursor-pointer"
              aria-label="Exit full view"
            >
              <Minimize2 size={14} />
              <span className="hidden sm:inline">Exit full view</span>
              <X size={14} className="sm:hidden" />
            </button>
          </header>

          <div
            ref={scrollRef}
            className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-4 sm:px-6 py-6 sm:py-8"
          >
            <div className="w-full max-w-3xl mx-auto flex flex-col gap-8 sm:gap-10">
              {messages.map((message, index) => {
                const isLast = index === messages.length - 1;
                const isUser = message.role === "user";

                if (isUser) {
                  return (
                    <div key={message.id} className="flex justify-center w-full">
                      <div className="w-full max-w-2xl rounded-2xl bg-surface-container-high/70 border border-outline-variant/25 px-4 py-3 sm:px-5 sm:py-3.5 shadow-sm">
                        <p className="text-[11px] font-semibold uppercase tracking-wide text-on-surface-variant/70 mb-1.5">
                          You
                        </p>
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
                  <div key={message.id} className="flex justify-center w-full">
                    <div className="w-full max-w-2xl text-left">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-on-surface-variant/70 mb-2">
                        Assistant
                      </p>

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
                        <div className="min-h-[2rem]">
                          <ResponseContent
                            isThinking={false}
                            isStreaming={showStreaming}
                            data={responseData}
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
                  <div className="w-full max-w-2xl flex items-center gap-2 text-error text-sm">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {lastAssistant?.content && !isStreaming && !error && (
            <footer className="shrink-0 border-t border-outline-variant/20 px-4 sm:px-6 py-3">
              <div className="w-full max-w-3xl mx-auto">
                <ActionButtons textToCopy={lastAssistant.content} onFullView={onClose} />
              </div>
            </footer>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
