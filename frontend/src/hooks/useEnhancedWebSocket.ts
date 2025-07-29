import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketService } from '@/services/EnhancedWebSocket';
import { toast } from '@/components/ui/use-toast';

type MessageHandler = (message: any) => void;

export const useEnhancedWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const messageHandlers = useRef<Set<MessageHandler>>(new Set());

  // Handle connection state
  useEffect(() => {
    const handleStateChange = (state: string) => {
      setIsConnected(state === 'connected');
      if (state === 'error') {
        toast({
          title: 'Connection Error',
          description: 'Failed to connect to the server. Reconnecting...',
          variant: 'destructive',
        });
      }
    };
    
    const unsubscribe = webSocketService.onStateChange(handleStateChange);
    return () => unsubscribe();
  }, []);

  // Message handling
  const onMessage = useCallback((handler: MessageHandler) => {
    messageHandlers.current.add(handler);
    const unsubscribe = webSocketService.onMessage(handler);
    return () => {
      messageHandlers.current.delete(handler);
      unsubscribe();
    };
  }, []);

  // Send message
  const send = useCallback((message: any) => {
    webSocketService.send(message);
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      messageHandlers.current.clear();
    };
  }, []);

  return {
    isConnected,
    onMessage,
    send,
  };
};

export default useEnhancedWebSocket;
