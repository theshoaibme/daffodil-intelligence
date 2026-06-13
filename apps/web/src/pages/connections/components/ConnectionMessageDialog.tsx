import { useEffect, useMemo, useRef, useState } from "react";
import { Mail, Send, X } from "lucide-react";
import { useAuth } from "@context";
import {
  buildFormalTemplate,
  formatFormalMessage,
  formatMessageDate,
  formalSalutation,
  type MessagePurpose,
} from "../lib/formalMessageTemplates";
import type { ConnectionMessage, ResearchConnection } from "../types";

interface ConnectionMessageDialogProps {
  connection: ResearchConnection | null;
  messages: ConnectionMessage[];
  onClose: () => void;
  onSend: (payload: {
    subject: string;
    salutation: string;
    body: string;
    closing: string;
    purpose?: string;
  }) => void;
}

const PURPOSE_OPTIONS: { id: MessagePurpose; label: string }[] = [
  { id: "collaboration", label: "Collaboration inquiry" },
  { id: "research-discussion", label: "Research discussion" },
  { id: "institutional-inquiry", label: "Institutional partnership" },
];

function normalizeMessage(message: ConnectionMessage): ConnectionMessage {
  if (message.subject && message.salutation) return message;
  return {
    ...message,
    subject: message.subject || "Correspondence",
    salutation: message.salutation || "Dear Colleague,",
    closing: message.closing || "Sincerely,",
    body: message.body,
  };
}

export function ConnectionMessageDialog({
  connection,
  messages,
  onClose,
  onSend,
}: ConnectionMessageDialogProps) {
  const { user } = useAuth();
  const senderName = user?.full_name?.trim() || user?.email?.split("@")[0] || "Research Scholar";

  const [purpose, setPurpose] = useState<MessagePurpose>("collaboration");
  const [subject, setSubject] = useState("");
  const [salutation, setSalutation] = useState("");
  const [body, setBody] = useState("");
  const [closing, setClosing] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  const thread = useMemo(() => messages.map(normalizeMessage), [messages]);

  const preview = useMemo(() => {
    if (!connection) return "";
    return formatFormalMessage({
      subject,
      salutation: salutation.trim() || formalSalutation(connection),
      body,
      closing,
    });
  }, [subject, salutation, body, closing, connection]);

  useEffect(() => {
    if (!connection) return;
    const template = buildFormalTemplate("collaboration", connection, senderName);
    setPurpose("collaboration");
    setSubject(template.subject);
    setSalutation(formalSalutation(connection));
    setBody(template.body);
    setClosing(template.closing);
  }, [connection, senderName]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [thread, connection]);

  if (!connection) return null;

  const applyTemplate = (nextPurpose: MessagePurpose) => {
    setPurpose(nextPurpose);
    const template = buildFormalTemplate(nextPurpose, connection, senderName);
    setSubject(template.subject);
    setSalutation(formalSalutation(connection));
    setBody(template.body);
    setClosing(template.closing);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) return;
    onSend({
      subject: subject.trim(),
      salutation: salutation.trim() || formalSalutation(connection),
      body: body.trim(),
      closing: closing.trim(),
      purpose,
    });
    applyTemplate(purpose);
  };

  const fieldClass =
    "w-full rounded-xl border border-outline-variant/15 bg-surface-container-low px-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30";

  return (
    <div className="fixed inset-0 z-[80] flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="connection-message-title"
        className="flex w-full max-w-2xl flex-col overflow-hidden rounded-3xl bg-surface-container-lowest shadow-xl max-h-[90vh]"
      >
        <div className="flex items-start justify-between gap-3 border-b border-outline-variant/10 px-5 py-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary">
              <Mail size={16} />
              <span className="text-xs font-semibold uppercase tracking-wide">Formal correspondence</span>
            </div>
            <h2 id="connection-message-title" className="mt-1 truncate text-lg font-semibold text-on-surface">
              To {connection.name}
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              Professional academic inquiry regarding shared research
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

        {thread.length > 0 && (
          <div
            ref={listRef}
            className="space-y-4 overflow-y-auto border-b border-outline-variant/10 px-5 py-4 max-h-[220px]"
          >
            {thread.map((message) => (
              <article
                key={message.id}
                className="rounded-2xl border border-outline-variant/10 bg-surface-container-low/60 px-4 py-3"
              >
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-on-surface-variant">
                  <span className="font-semibold text-on-surface">Re: {message.subject}</span>
                  <time dateTime={message.sentAt}>{formatMessageDate(message.sentAt)}</time>
                </div>
                <div className="space-y-2 whitespace-pre-wrap text-sm leading-relaxed text-on-surface">
                  <p>{message.salutation}</p>
                  <p>{message.body}</p>
                  <p className="text-on-surface-variant">{message.closing}</p>
                </div>
              </article>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col overflow-y-auto">
          <div className="space-y-4 px-5 py-4">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
                Purpose
              </label>
              <div className="flex flex-wrap gap-1.5">
                {PURPOSE_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => applyTemplate(option.id)}
                    className={`cursor-pointer rounded-full border-0 px-3 py-1.5 text-xs font-semibold transition-colors ${
                      purpose === option.id
                        ? "bg-primary text-on-primary"
                        : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="formal-subject" className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
                Subject
              </label>
              <input
                id="formal-subject"
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className={fieldClass}
                required
              />
            </div>

            <div>
              <label htmlFor="formal-salutation" className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
                Salutation
              </label>
              <input
                id="formal-salutation"
                type="text"
                value={salutation}
                onChange={(e) => setSalutation(e.target.value)}
                className={fieldClass}
              />
            </div>

            <div>
              <label htmlFor="formal-body" className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
                Message body
              </label>
              <textarea
                id="formal-body"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={7}
                required
                className={`${fieldClass} min-h-[160px] resize-y leading-relaxed`}
                placeholder="Write your formal inquiry..."
              />
            </div>

            <div>
              <label htmlFor="formal-closing" className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
                Closing & signature
              </label>
              <textarea
                id="formal-closing"
                value={closing}
                onChange={(e) => setClosing(e.target.value)}
                rows={3}
                className={`${fieldClass} resize-y leading-relaxed`}
              />
            </div>

            <div>
              <p className="mb-1.5 text-xs font-semibold text-on-surface-variant">Preview</p>
              <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-low/50 px-4 py-3">
                <p className="mb-2 text-[11px] font-semibold text-on-surface-variant">
                  Subject: {subject || "—"}
                </p>
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-on-surface">
                  {preview}
                </pre>
              </div>
            </div>
          </div>

          <div className="mt-auto flex items-center justify-between gap-3 border-t border-outline-variant/10 px-5 py-4">
            <p className="text-[11px] text-on-surface-variant">
              Messages follow a professional academic format suitable for research outreach.
            </p>
            <button
              type="submit"
              disabled={!subject.trim() || !body.trim()}
              className="inline-flex shrink-0 items-center gap-2 rounded-full border-0 bg-primary px-5 py-2.5 text-sm font-semibold text-on-primary disabled:opacity-50 cursor-pointer"
            >
              <Send size={15} />
              Send correspondence
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
