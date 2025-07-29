import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import useEnhancedWebSocket from '@/hooks/useEnhancedWebSocket';
import { 
  Message, 
  MessageStatus, 
  TypingUser, 
  User, 
  Conversation, 
  ChatContextType as ChatContextTypeImport,
  ExtendedMessage
} from '@/types/chat';

const ChatContext = createContext<ChatContextTypeImport | undefined>(undefined);

const TYPING_TIMEOUT = 3000; // 3 seconds

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const { send, onMessage, isConnected } = useEnhancedWebSocket();
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  const currentUserId = 'current-user'; // In a real app, get this from auth context
  const pageRef = useRef(1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle incoming messages
  useEffect(() => {
    if (!isConnected) return;
    
    const handleIncomingMessage = (message: any) => {
      console.log('Received message:', message);
      
      if (message.type === 'message') {
        setMessages(prev => [{
          ...message,
          id: message.id || `msg-${Date.now()}`,
          status: 'delivered' as const,
          timestamp: message.timestamp || new Date().toISOString(),
        }, ...prev]);
      } else if (message.type === 'typing' && message.userId !== currentUserId) {
        // Update typing users
        setTypingUsers(prev => {
          const existingUser = prev.find(u => u.userId === message.userId);
          const now = Date.now();
          
          if (existingUser) {
            return prev.map(u => 
              u.userId === message.userId 
                ? { ...u, lastTypingTime: now } 
               : u
            );
          } else {
            return [
              ...prev,
              {
                userId: message.userId,
                name: message.userName || 'User',
                lastTypingTime: now
              }
            ];
          }
        });
      }
    };

    const unsubscribe = onMessage(handleIncomingMessage);
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [onMessage, isConnected]);

  // Clean up typing users and handle reconnection
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setTypingUsers(prev => 
        prev.filter(user => now - user.lastTypingTime < TYPING_TIMEOUT)
      );
    }, 1000);

    // Cleanup on unmount
    return () => {
      clearInterval(interval);
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  // Handle typing indicator with debounce
  const handleSetTyping = useCallback((typing: boolean) => {
    setIsTyping(typing);
    
    // Only send typing events when connected
    if (isConnected) {
      send({
        type: 'typing',
        userId: currentUserId,
        isTyping: typing,
        timestamp: new Date().toISOString(),
      });
      
      typingTimeoutRef.current = setTimeout(() => {
        setIsTyping(false);
      }, TYPING_TIMEOUT);
    }
  }, [send, isConnected]);

  // Send a message with optional reply
  const sendMessage = useCallback((content: string, replyToId?: string) => {
    if (!content.trim()) return;
    
    const tempId = `temp-${Date.now()}`;
    const newMessage: ExtendedMessage = {
      id: '',
      content,
      userId: currentUserId,
      user: { id: currentUserId, name: 'You' },
      status: 'sending' as const,
      timestamp: new Date().toISOString(),
      reactions: {},
      isPinned: false,
    };

    // Add replyTo reference if provided
    if (replyToId) {
      const repliedMessage = messages.find(m => m.id === replyToId);
      if (repliedMessage) {
        newMessage.replyTo = {
          id: repliedMessage.id,
          content: repliedMessage.content,
          user: repliedMessage.user
        };
      }
    }

    // Optimistic update
    setMessages(prev => [newMessage, ...prev]);
    
    // Reset typing
    handleSetTyping(false);
    
    // Send the message
    send({
      type: 'message',
      ...newMessage
    });
    
    // Simulate message delivery
    setTimeout(() => {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === tempId 
            ? { ...msg, status: 'sent' as const, id: `msg-${Date.now()}` } 
            : msg
        )
      );
    }, 500);
  }, [send, handleSetTyping, messages]);
  
  // Edit a message
  const editMessage = useCallback((messageId: string, content: string) => {
    if (!content.trim()) return;
    
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content, isEdited: true }
          : msg
      )
    );
    
    // Send update to server
    send({
      type: 'edit_message',
      messageId,
      content,
      timestamp: new Date().toISOString()
    });
  }, [send]);
  
  // Delete a message
  const deleteMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    
    // Send delete to server
    send({
      type: 'delete_message',
      messageId,
      timestamp: new Date().toISOString()
    });
  }, [send]);
  
  // Add or remove reaction to a message
  const reactToMessage = useCallback((messageId: string, emoji: string) => {
    setMessages(prev => 
      prev.map(msg => {
        if (msg.id !== messageId) return msg;
        
        const reactions = { ...(msg.reactions || {}) };
        const userReactionIndex = reactions[emoji]?.indexOf(currentUserId) ?? -1;
        
        if (userReactionIndex > -1) {
          // Remove reaction if user already reacted with this emoji
          const updatedReactions = [...(reactions[emoji] || [])];
          updatedReactions.splice(userReactionIndex, 1);
          
          if (updatedReactions.length === 0) {
            delete reactions[emoji];
          } else {
            reactions[emoji] = updatedReactions;
          }
        } else {
          // Add reaction
          reactions[emoji] = [...(reactions[emoji] || []), currentUserId];
        }
        
        return { ...msg, reactions };
      })
    );
    
    // Send reaction to server
    send({
      type: 'react_to_message',
      messageId,
      emoji,
      userId: currentUserId,
      timestamp: new Date().toISOString()
    });
  }, [send, currentUserId]);
  
  // Toggle message pin status
  const togglePinMessage = useCallback((messageId: string) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, isPinned: !msg.isPinned }
          : msg
      )
    );
    
    // Send pin update to server
    send({
      type: 'toggle_pin_message',
      messageId,
      timestamp: new Date().toISOString()
    });
  }, [send]);

  // Load more messages for pagination
  const loadMoreMessages = useCallback(async () => {
    if (!currentConversation || isLoadingMessages || !hasMoreMessages) return;
    
    try {
      setIsLoadingMessages(true);
      // In a real app, you would fetch more messages from your API
      // const response = await messagesApi.getByConversationId(currentConversation.id, {
      //   page: pageRef.current + 1,
      //   limit: 20,
      // });
      // 
      // if (response.data.length === 0) {
      //   setHasMoreMessages(false);
      //   return;
      // }
      // 
      // setMessages(prev => [...prev, ...response.data]);
      // pageRef.current += 1;
    } catch (error) {
      console.error('Failed to load more messages:', error);
    } finally {
      setIsLoadingMessages(false);
    }
  }, [currentConversation, hasMoreMessages, isLoadingMessages]);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, scrollToBottom]);

  // Load initial conversations
  useEffect(() => {
    const loadConversations = async () => {
      try {
        // In a real app, you would fetch conversations from your API
        // const response = await conversationsApi.getAll();
        // setConversations(response.data);
      } catch (error) {
        console.error('Failed to load conversations:', error);
      }
    };

    loadConversations();
  }, []);

  return (
    <ChatContext.Provider value={{
      messages,
      sendMessage,
      isTyping,
      setTyping: handleSetTyping,
      typingUsers,
      isConnected,
      currentConversation,
      setCurrentConversation,
      conversations,
      loadMoreMessages,
      hasMoreMessages,
      isLoadingMessages,
    }}>
      {children}
      <div ref={messagesEndRef} />
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
