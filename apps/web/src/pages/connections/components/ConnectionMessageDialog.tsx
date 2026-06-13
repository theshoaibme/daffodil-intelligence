import { useEffect, useRef, useState } from "react";
import { Send, X } from "lucide-react";
import type { ConnectionMessage, ResearchConnection } from "../types";

interface ConnectionMessageDialogProps {
  connection: ResearchConnection | null;
  messages: ConnectionMessage[];
  onClose: () => void;
  onSend: (body: string) => void;
}

export function ConnectionMessageDialog({
  connection,
  messages,
  onClose,
  onSend,
}: ConnectionMessageDialogProps) {
  const [draft, setDraft] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!connection) setDraft("");
  }, [connection]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, connection]);

  if (!connection) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    onSend(draft);
    setDraft("");
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="connection-message-title"
        className="flex w-full max-w-lg flex-col overflow-hidden rounded-3xl bg-surface-container-lowest shadow-xl max-h-[85vh]"
      >
        <div className="flex items-start justify-between gap-3 border-b border-outline-variant/10 px-5 py-4">
          <div className="min-w-0">
            <h2 id="connection-message-title" className="truncate text-lg font-semibold text-on-surface">
              Message {connection.name}
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              Discuss collaboration around shared research papers
            </p>
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

        <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-5 py-4 min-h-[220px] max-h-[360px]">
          {messages.length === 0 ? (
            <p className="text-sm text-on-surface-variant text-center py-8">
              Start a conversation about {connection.featuredPaper?.title ?? "shared research interests"}.
            </p>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary/10 px-4 py-2.5 text-sm text-on-surface">
                  {message.body}
                </div>
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-outline-variant/10 p-4 flex gap-2">
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Write a message..."
            className="flex-1 rounded-xl border-0 bg-surface-container-low px-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <button
            type="submit"
            disabled={!draft.trim()}
            className="inline-flex items-center justify-center rounded-full border-0 bg-primary px-4 py-2.5 text-on-primary disabled:opacity-50 cursor-pointer"
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
