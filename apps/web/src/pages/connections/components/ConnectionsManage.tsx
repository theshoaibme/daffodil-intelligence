import { useState } from "react";
import { ConnectionsInbox } from "./ConnectionsInbox";
import { ConnectionsNetwork } from "./ConnectionsNetwork";
import { useConnectionsNetwork } from "../hooks/useConnectionsNetwork";
import { useAuth } from "@context";
import type { ResearchConnection } from "../types";
import { ConnectionChatDialog } from "./ConnectionChatDialog";

type StudioTab = "network" | "messages";

export function ConnectionsManage() {
  const { isAuthenticated } = useAuth();
  const network = useConnectionsNetwork(isAuthenticated);
  const {
    conversations,
    conversationsLoading,
    getStatus,
    loadMessages,
    getMessages,
    sendMessage,
  } = network;

  const [tab, setTab] = useState<StudioTab>("network");
  const [activeChat, setActiveChat] = useState<ResearchConnection | null>(null);

  const openChat = (connection: ResearchConnection) => {
    setActiveChat(connection);
    void loadMessages(connection.id);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {(
          [
            { id: "network", label: "Network" },
            { id: "messages", label: "Messages" },
          ] as const
        ).map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`cursor-pointer rounded-full border-0 px-4 py-2 text-sm font-semibold transition-colors ${
              tab === id
                ? "bg-primary text-on-primary"
                : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
            }`}
          >
            {label}
            {id === "messages" && conversations.length > 0 ? ` (${conversations.length})` : ""}
          </button>
        ))}
      </div>

      {tab === "network" ? (
        <ConnectionsNetwork workspace network={network} />
      ) : (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-on-surface">Your conversations</h3>
            <p className="text-sm text-on-surface-variant">
              Chat with connected researchers and institutions. Replies appear once you are connected.
            </p>
          </div>
          <ConnectionsInbox
            conversations={conversations}
            loading={conversationsLoading}
            activeId={activeChat?.id}
            onSelect={(connection) => {
              setActiveChat(connection);
              openChat(connection);
            }}
          />
        </div>
      )}

      {activeChat && tab === "messages" && (
        <ConnectionChatDialog
          connection={activeChat}
          status={getStatus(activeChat.id)}
          messages={getMessages(activeChat.id)}
          onClose={() => setActiveChat(null)}
          onSend={(payload) => sendMessage(activeChat.id, payload)}
        />
      )}
    </div>
  );
}
