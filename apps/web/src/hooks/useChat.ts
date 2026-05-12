import { useCallback, useRef } from 'react';
import { useChatStore } from '../store';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';

let messageIdCounter = Date.now();

function generateMessageId(): number {
  return ++messageIdCounter;
}

export function useChat() {
  const { messages, addMessage, isLoading, setLoading, clear } = useChatStore();
  const { isConnected, connect } = useWebSocket();
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string, agentType: string = 'supervisor') => {
    addMessage({ id: generateMessageId(), role: 'user', content });
    setLoading(true);

    try {
      const response = await api.chat(content, agentType);
      addMessage({
        id: generateMessageId(),
        role: 'assistant',
        content: response.response,
        agent: response.agent,
      });
    } catch (error) {
      addMessage({
        id: generateMessageId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      });
    }

    setLoading(false);
  }, [addMessage, setLoading]);

  const streamMessage = useCallback(async (content: string, agentType: string = 'supervisor') => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    addMessage({ id: generateMessageId(), role: 'user', content });
    setLoading(true);

    try {
      const response = await fetch(`${api.getBaseUrl()}/api/agents/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(api.getToken() ? { 'Authorization': `Bearer ${api.getToken()}` } : {})
        },
        body: JSON.stringify({ message: content, agent_type: agentType }),
        signal: abortControllerRef.current.signal,
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let responseText = '';
      const assistantMsgId = generateMessageId();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          responseText += chunk;
          addMessage({
            id: assistantMsgId,
            role: 'assistant',
            content: responseText,
          });
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        addMessage({
          id: generateMessageId(),
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        });
      }
    }

    setLoading(false);
    abortControllerRef.current = null;
  }, [addMessage, setLoading]);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    messages,
    isLoading,
    isConnected,
    sendMessage,
    streamMessage,
    cancelStream,
    clear,
    connect,
  };
}