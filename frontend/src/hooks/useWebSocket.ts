import { useEffect, useRef, useCallback } from 'react';
import { webSocketService, MessageCallback, ErrorCallback } from '@/services/websocket';
import { toast } from '@/components/ui/use-toast';

export const useWebSocket = () => {
  const messageCallbacks = useRef<Map<string, MessageCallback>>(new Map());
  const errorCallbacks = useRef<Set<ErrorCallback>>(new Set());

  // Handle incoming messages
  const onMessage = useCallback((callback: MessageCallback) => {
    const id = webSocketService.onMessage(callback);
    messageCallbacks.current.set(id, callback);
    
    return () => {
      webSocketService.offMessage(id);
      messageCallbacks.current.delete(id);
    };
  }, []);

  // Handle errors
  const onError = useCallback((callback: ErrorCallback) => {
    const unsubscribe = webSocketService.onError(callback);
    errorCallbacks.current.add(callback);
    
    return () => {
      unsubscribe();
      errorCallbacks.current.delete(callback);
    };
  }, []);

  // Send message
  const send = useCallback((message: any) => {
    webSocketService.send(message);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    // Default error handler
    const defaultErrorHandler: ErrorCallback = (error) => {
      console.error('WebSocket error:', error);
      toast({
        title: 'Connection Error',
        description: 'Failed to connect to the server. Please try again later.',
        variant: 'destructive',
      });
    };

    // Add default error handler
    const unsubscribeError = webSocketService.onError(defaultErrorHandler);
    errorCallbacks.current.add(defaultErrorHandler);

    return () => {
      // Clean up all message callbacks
      messageCallbacks.current.forEach((_, id) => {
        webSocketService.offMessage(id);
      });
      messageCallbacks.current.clear();

      // Clean up all error callbacks
      errorCallbacks.current.forEach(callback => {
        if (callback !== defaultErrorHandler) {
          webSocketService.onError(callback);
        }
      });
      errorCallbacks.current.clear();

      // Remove default error handler
      unsubscribeError();
    };
  }, []);

  return {
    send,
    onMessage,
    onError,
    isConnected: webSocketService.isConnected,
  };
};

export default useWebSocket;
