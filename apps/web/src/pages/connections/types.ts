export type ConnectionKind = "researcher" | "institution";

export type ConnectionStatus = "available" | "pending" | "connected";

export type MessageDirection = "outgoing" | "incoming";
export type MessageType = "chat" | "formal";

export interface ResearchConnection {
  id: string;
  kind: ConnectionKind;
  name: string;
  subtitle: string;
  focus: string;
  paperCount: number;
  citations: number;
  paperIds: string[];
  featuredPaper?: { id: string; title: string };
}

export interface ConnectionMessage {
  id: string;
  connectionId: string;
  subject: string;
  salutation: string;
  body: string;
  closing: string;
  sentAt: string;
  direction: MessageDirection;
  senderName?: string;
  messageType: MessageType;
  purpose?: string;
}

export interface ConnectionConversation {
  targetId: string;
  kind: ConnectionKind;
  name: string;
  subtitle: string;
  focus: string;
  status: ConnectionStatus;
  lastMessage?: ConnectionMessage;
  messageCount: number;
}
