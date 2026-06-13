export type ConnectionKind = "researcher" | "institution";

export type ConnectionStatus = "available" | "pending" | "connected";

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
  body: string;
  sentAt: string;
  direction: "outgoing";
}
