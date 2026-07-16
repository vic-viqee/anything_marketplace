import { useEffect, useRef, useCallback, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data: Record<string, unknown>;
}

type MessageHandler = (message: WebSocketMessage) => void;

export function useWebSocket(
  token: string | null,
  onMessage?: MessageHandler
) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const onMessageRef = useRef(onMessage);
  const reconnectFnRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const reconnect = useCallback(() => {
    if (!token || typeof window === 'undefined') return;

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = API_URL.replace('http', 'ws') + '/ws/chat?token=' + token;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.debug('[ws] open', wsUrl);
        setConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          console.debug('[ws] message', message);
          setLastMessage(message);
          onMessageRef.current?.(message);
        } catch (error) {
          console.debug('[ws] parse error', error, event.data);
        }
      };

      wsRef.current.onclose = (event) => {
        console.debug('[ws] close', event.code, event.reason);
        setConnected(false);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectFnRef.current?.();
        }, 3000);
      };

      wsRef.current.onerror = (event) => {
        console.debug('[ws] error', event);
        wsRef.current?.close();
      };
    } catch (error) {
      console.debug('[ws] connect error', error);
    }
  }, [token]);

  useEffect(() => {
    reconnectFnRef.current = reconnect;
  }, [reconnect]);

  useEffect(() => {
    reconnect();
    return () => disconnect();
  }, [reconnect, disconnect]);

  return {
    connected,
    lastMessage,
    send: (data: WebSocketMessage) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(data));
      }
    },
    ping: () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', data: {} }));
      }
    },
    disconnect,
    reconnect,
  };
}
