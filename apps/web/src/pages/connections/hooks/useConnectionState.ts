import { useCallback, useEffect, useState } from "react";
import type { ConnectionMessage, ConnectionStatus } from "../types";

const STATUS_KEY = "research-connection-status-v1";
const MESSAGES_KEY = "research-connection-messages-v1";

function readStatuses(): Record<string, ConnectionStatus> {
  try {
    const raw = localStorage.getItem(STATUS_KEY);
    return raw ? (JSON.parse(raw) as Record<string, ConnectionStatus>) : {};
  } catch {
    return {};
  }
}

function readMessages(): ConnectionMessage[] {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY);
    return raw ? (JSON.parse(raw) as ConnectionMessage[]) : [];
  } catch {
    return [];
  }
}

export function useConnectionState() {
  const [statuses, setStatuses] = useState<Record<string, ConnectionStatus>>(readStatuses);
  const [messages, setMessages] = useState<ConnectionMessage[]>(readMessages);

  useEffect(() => {
    localStorage.setItem(STATUS_KEY, JSON.stringify(statuses));
  }, [statuses]);

  useEffect(() => {
    localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
  }, [messages]);

  const getStatus = useCallback(
    (connectionId: string): ConnectionStatus => statuses[connectionId] ?? "available",
    [statuses],
  );

  const connect = useCallback((connectionId: string) => {
    setStatuses((prev) => {
      const current = prev[connectionId] ?? "available";
      if (current === "connected") return prev;
      return { ...prev, [connectionId]: current === "pending" ? "connected" : "pending" };
    });
  }, []);

  const acceptConnection = useCallback((connectionId: string) => {
    setStatuses((prev) => ({ ...prev, [connectionId]: "connected" }));
  }, []);

  const sendMessage = useCallback(
    (
      connectionId: string,
      payload: {
        subject: string;
        salutation: string;
        body: string;
        closing: string;
        purpose?: string;
      },
    ) => {
      const subject = payload.subject.trim();
      const body = payload.body.trim();
      if (!subject || !body) return;

      const message: ConnectionMessage = {
        id: `${connectionId}-${Date.now()}`,
        connectionId,
        subject,
        salutation: payload.salutation.trim(),
        body,
        closing: payload.closing.trim(),
        purpose: payload.purpose,
        sentAt: new Date().toISOString(),
        direction: "outgoing",
      };
      setMessages((prev) => [...prev, message]);
      setStatuses((prev) => {
        const current = prev[connectionId] ?? "available";
        if (current === "connected") return prev;
        return { ...prev, [connectionId]: "pending" };
      });
    },
    [],
  );

  const getMessages = useCallback(
    (connectionId: string) => messages.filter((m) => m.connectionId === connectionId),
    [messages],
  );

  const connectedCount = Object.values(statuses).filter((s) => s === "connected").length;

  return {
    getStatus,
    connect,
    acceptConnection,
    sendMessage,
    getMessages,
    connectedCount,
  };
}
