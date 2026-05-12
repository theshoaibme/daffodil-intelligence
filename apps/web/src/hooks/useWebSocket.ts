import { useEffect, useRef, useCallback, useState } from 'react';

interface WebSocketMessage {
  type?: string;
  [key: string]: unknown;
}

interface UseWebSocketOptions {
  onMessage?: (data: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const userIdRef = useRef<number | null>(null);
  
  const onMessageRef = useRef(onMessage);
  const onConnectRef = useRef(onConnect);
  const onDisconnectRef = useRef(onDisconnect);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onMessageRef.current = onMessage;
    onConnectRef.current = onConnect;
    onDisconnectRef.current = onDisconnect;
    onErrorRef.current = onError;
  }, [onMessage, onConnect, onDisconnect, onError]);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback((userId: number) => {
    clearReconnectTimeout();
    
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    userIdRef.current = userId;

    const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectCountRef.current = 0;
      onConnectRef.current?.();
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(data);
        onMessageRef.current?.(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      onDisconnectRef.current?.();

      if (event.code !== 1000 && userIdRef.current !== null) {
        const shouldReconnect = reconnectCountRef.current < maxReconnectAttempts;
        if (shouldReconnect) {
          reconnectCountRef.current += 1;
          console.log(`Reconnecting... Attempt ${reconnectCountRef.current}/${maxReconnectAttempts}`);
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (userIdRef.current !== null) {
              connect(userIdRef.current);
            }
          }, reconnectInterval);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onErrorRef.current?.(error);
    };

    wsRef.current = ws;
  }, [reconnectInterval, maxReconnectAttempts, clearReconnectTimeout]);

  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    reconnectCountRef.current = maxReconnectAttempts;
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
    userIdRef.current = null;
  }, [maxReconnectAttempts, clearReconnectTimeout]);

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message }));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    return () => {
      clearReconnectTimeout();
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
      }
    };
  }, [clearReconnectTimeout]);

  return { isConnected, lastMessage, connect, disconnect, send };
}