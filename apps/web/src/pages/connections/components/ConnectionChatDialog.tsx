import { useEffect, useMemo, useRef, useState } from "react";
import { FileText, MessageSquare, Send, X } from "lucide-react";
import { useAuth } from "@context";
import { formatMessageDate } from "../lib/formalMessageTemplates";
import type { ConnectionMessage, ConnectionStatus, ResearchConnection } from "../types";

interface ConnectionChatDialogProps {
  connection: ResearchConnection | null;
  status: ConnectionStatus;
  messages: ConnectionMessage[];
  onClose: () => void;
  onSend: (payload: {
    body: string;
    message_type: "chat" | "formal";
    subject?: string;
    salutation?: string;
    closing?: string;
    purpose?: string;
  }) => Promise<unknown>;
}

function messagePreview(message: ConnectionMessage): string {
  if (message.messageType === "chat") {
    return message.body;
  }
  return [message.salutation, message.body, message.closing].filter(Boolean).join("\n\n");
}

function ChatBubble({ message, selfLabel }: { message: ConnectionMessage; selfLabel: string }) {
  const isOutgoing = message.direction === "outgoing";
  const label = isOutgoing ? selfLabel : message.senderName || "Connection";

  return (
    <article className={`flex flex-col gap-1 ${isOutgoing ? "items-end" : "items-start"}`}>
      <div className="flex items-center gap-2 text-[11px] text-on-surface-variant">
        <span className="font-semibold text-on-surface">{label}</span>
        <time dateTime={message.sentAt}>{formatMessageDate(message.sentAt)}</time>
      </div>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isOutgoing
            ? "chat-bubble-user text-on-surface rounded-br-md"
            : "bg-surface-container-high text-on-surface rounded-bl-md"
        }`}
      >
        {message.messageType === "formal" && message.subject ? (
          <p className="mb-2 text-[11px] font-semibold text-on-surface-variant">Re: {message.subject}</p>
        ) : null}
        {messagePreview(message)}
      </div>
    </article>
  );
}

export function ConnectionChatDialog({
  connection,
  status,
  messages,
  onClose,
  onSend,
}: ConnectionChatDialogProps) {
  const { user } = useAuth();
  const selfLabel = user?.full_name?.trim() || user?.email?.split("@")[0] || "You";
  const [draft, setDraft] = useState("");
  const [formalOpen, setFormalOpen] = useState(false);
  const [subject, setSubject] = useState("");
  const [salutation, setSalutation] = useState("Dear Colleague,");
  const [closing, setClosing] = useState(`Sincerely,\n${selfLabel}`);
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const thread = useMemo(() => messages, [messages]);
  const canChat = status === "connected";

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [thread, connection]);

  useEffect(() => {
    if (!connection) return;
    setDraft("");
    setFormalOpen(false);
    setSubject(`Research discussion — ${connection.focus}`);
  }, [connection]);

  if (!connection) return null;

  const fieldClass =
    "w-full rounded-xl border border-outline-variant/15 bg-surface-container-low px-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30";

  const handleQuickSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !canChat || sending) return;
    setSending(true);
    try {
      await onSend({ body: text, message_type: "chat" });
      setDraft("");
    } finally {
      setSending(false);
    }
  };

  const handleFormalSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canChat || sending || !draft.trim()) return;
    setSending(true);
    try {
      await onSend({
        body: draft.trim(),
        message_type: "formal",
        subject: subject.trim(),
        salutation: salutation.trim(),
        closing: closing.trim(),
      });
      setDraft("");
      setFormalOpen(false);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="connection-chat-title"
        className="flex w-full max-w-2xl flex-col overflow-hidden rounded-3xl bg-surface-container-lowest shadow-xl max-h-[90vh]"
      >
        <div className="flex items-start justify-between gap-3 border-b border-outline-variant/10 px-5 py-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary">
              <MessageSquare size={16} />
              <span className="text-xs font-semibold uppercase tracking-wide">Research chat</span>
            </div>
            <h2 id="connection-chat-title" className="mt-1 truncate text-lg font-semibold text-on-surface">
              {connection.name}
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5 truncate">{connection.subtitle}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border-0 bg-transparent p-2 text-on-surface-variant hover:bg-surface-container-high cursor-pointer"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {!canChat ? (
          <div className="px-5 py-10 text-center text-sm text-on-surface-variant">
            {status === "pending"
              ? "This connection is pending. Accept the request to start chatting."
              : "Connect with this researcher or institution before starting a conversation."}
          </div>
        ) : (
          <>
            <div ref={listRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-4 min-h-[280px] max-h-[50vh]">
              {thread.length === 0 ? (
                <div className="flex h-full min-h-[220px] flex-col items-center justify-center gap-2 text-center text-sm text-on-surface-variant">
                  <MessageSquare size={28} className="text-primary/50" />
                  <p>No messages yet. Say hello and introduce your research interests.</p>
                </div>
              ) : (
                thread.map((message) => (
                  <ChatBubble key={message.id} message={message} selfLabel={selfLabel} />
                ))
              )}
            </div>

            <div className="border-t border-outline-variant/10 px-5 py-4 space-y-3">
              <form onSubmit={handleQuickSend} className="flex items-end gap-2">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={2}
                  placeholder="Write a message..."
                  className={`${fieldClass} min-h-[52px] resize-none flex-1`}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void handleQuickSend(e);
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={!draft.trim() || sending}
                  className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-0 bg-primary text-on-primary disabled:opacity-50 cursor-pointer"
                  aria-label="Send message"
                >
                  <Send size={16} />
                </button>
              </form>

              <button
                type="button"
                onClick={() => setFormalOpen((open) => !open)}
                className="inline-flex items-center gap-1.5 border-0 bg-transparent text-xs font-semibold text-primary hover:underline cursor-pointer"
              >
                <FileText size={13} />
                {formalOpen ? "Hide formal letter" : "Send formal correspondence"}
              </button>

              {formalOpen && (
                <form onSubmit={handleFormalSend} className="space-y-3 rounded-2xl bg-surface-container-low/60 p-4">
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Subject"
                    className={fieldClass}
                  />
                  <input
                    type="text"
                    value={salutation}
                    onChange={(e) => setSalutation(e.target.value)}
                    placeholder="Salutation"
                    className={fieldClass}
                  />
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    rows={5}
                    placeholder="Formal message body"
                    className={`${fieldClass} resize-y`}
                    required
                  />
                  <textarea
                    value={closing}
                    onChange={(e) => setClosing(e.target.value)}
                    rows={2}
                    placeholder="Closing"
                    className={`${fieldClass} resize-y`}
                  />
                  <button
                    type="submit"
                    disabled={!draft.trim() || sending}
                    className="inline-flex items-center gap-2 rounded-full border-0 bg-primary px-4 py-2 text-sm font-semibold text-on-primary disabled:opacity-50 cursor-pointer"
                  >
                    <Send size={14} />
                    Send formal letter
                  </button>
                </form>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
