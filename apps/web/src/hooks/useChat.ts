import { useCallback } from 'react';
import { useChatStore } from '../store';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';

export function useChat() {
  const { messages, addMessage, isLoading, setLoading, clear } = useChatStore();
  const { isConnected, connect } = useWebSocket();

  const sendMessage = useCallback(async (content: string, agentType: string = 'supervisor') => {
    addMessage({ id: Date.now(), role: 'user', content });
    setLoading(true);

    try {
      const response = await api.chat(content, agentType);
      addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        agent: response.agent,
      });
    } catch (error) {
      addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      });
    }

    setLoading(false);
  }, [addMessage, setLoading]);

  const streamMessage = useCallback(async (content: string, agentType: string = 'supervisor') => {
    addMessage({ id: Date.now(), role: 'user', content });
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/agents/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: content, agent_type: agentType }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let responseText = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          responseText += chunk;
          addMessage({
            id: Date.now() + 1,
            role: 'assistant',
            content: responseText,
          });
        }
      }
    } catch (error) {
      addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      });
    }

    setLoading(false);
  }, [addMessage, setLoading]);

  return {
    messages,
    isLoading,
    isConnected,
    sendMessage,
    streamMessage,
    clear,
    connect,
  };
}