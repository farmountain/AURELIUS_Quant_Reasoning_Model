import { createContext, useContext, useEffect, useRef, useCallback } from 'react';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children, token }) => {
  const ws = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = useRef(1000);
  const listeners = useRef({});

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = `${protocol}//${window.location.host}/ws?token=${token}`;
      
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts.current = 0;
        reconnectDelay.current = 1000;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const { type, payload } = data;
          
          if (listeners.current[type]) {
            listeners.current[type].forEach(callback => callback(payload));
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      attemptReconnect();
    }
  }, [token]);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttempts.current < maxReconnectAttempts) {
      reconnectAttempts.current++;
      setTimeout(() => {
        connect();
      }, reconnectDelay.current);
      reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
    }
  }, [connect]);

  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [token, connect]);

  const subscribe = useCallback((type, callback) => {
    if (!listeners.current[type]) {
      listeners.current[type] = [];
    }
    listeners.current[type].push(callback);

    return () => {
      listeners.current[type] = listeners.current[type].filter(cb => cb !== callback);
    };
  }, []);

  const send = useCallback((type, payload) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, payload }));
    }
  }, []);

  const value = {
    isConnected: ws.current?.readyState === WebSocket.OPEN,
    subscribe,
    send,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};
