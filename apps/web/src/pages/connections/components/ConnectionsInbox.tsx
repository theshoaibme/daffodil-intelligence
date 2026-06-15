import { Building2, GraduationCap, MessageSquare } from "lucide-react";
import { Loader } from "@ui";
import { formatMessageDate } from "../lib/formalMessageTemplates";
import type { ConnectionConversation, ResearchConnection } from "../types";

interface ConnectionsInboxProps {
  conversations: ConnectionConversation[];
  loading: boolean;
  activeId?: string | null;
  onSelect: (connection: ResearchConnection) => void;
}

function toResearchConnection(conversation: ConnectionConversation): ResearchConnection {
  return {
    id: conversation.targetId,
    kind: conversation.kind,
    name: conversation.name,
    subtitle: conversation.subtitle,
    focus: conversation.focus,
    paperCount: 0,
    citations: 0,
    paperIds: [],
  };
}

export function ConnectionsInbox({
  conversations,
  loading,
  activeId,
  onSelect,
}: ConnectionsInboxProps) {
  if (loading) {
    return (
      <div className="flex justify-center rounded-3xl bg-surface-container-low/50 p-10">
        <Loader variant="spinner" diameter={28} strokeWidth={3} color="primary" message="Loading chats..." />
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="rounded-3xl bg-surface-container-low/50 p-10 text-center text-sm text-on-surface-variant">
        <MessageSquare size={28} className="mx-auto mb-3 text-primary/50" />
        <p>No active chats yet.</p>
        <p className="mt-1">Connect with researchers in the network, then start a conversation here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {conversations.map((conversation) => {
        const Icon = conversation.kind === "institution" ? Building2 : GraduationCap;
        const preview = conversation.lastMessage;
        const isActive = activeId === conversation.targetId;

        return (
          <button
            key={conversation.targetId}
            type="button"
            onClick={() => onSelect(toResearchConnection(conversation))}
            className={`flex w-full items-start gap-3 rounded-2xl border-0 px-4 py-3 text-left transition-colors cursor-pointer ${
              isActive
                ? "bg-primary/10 ring-1 ring-primary/20"
                : "bg-surface-container-low hover:bg-surface-container"
            }`}
          >
            <div className="rounded-xl bg-surface-container-lowest p-2.5 text-primary">
              <Icon size={16} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-semibold text-on-surface">{conversation.name}</p>
                {preview ? (
                  <time className="shrink-0 text-[10px] text-on-surface-variant">
                    {formatMessageDate(preview.sentAt)}
                  </time>
                ) : null}
              </div>
              <p className="truncate text-xs text-on-surface-variant">{conversation.subtitle}</p>
              <p className="mt-1 line-clamp-2 text-xs text-on-surface-variant/90">
                {preview
                  ? preview.direction === "incoming"
                    ? `${preview.senderName || conversation.name}: ${preview.body}`
                    : `You: ${preview.body}`
                  : "No messages yet"}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
