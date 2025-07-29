import React, { useState, useRef, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Loader2, Wifi, WifiOff, AlertCircle, ArrowDown, RefreshCw, Users, X, Reply } from 'lucide-react';

import { useChat } from '@/contexts/ChatContext';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

// Connection status component
const ConnectionStatus = () => {
  const { isConnected } = useChat();
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center px-3 py-1 rounded-full text-xs font-medium bg-background border">
            {isConnected ? (
              <>
                <Wifi className="h-3 w-3 text-green-500 mr-1" />
                <span>Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3 w-3 text-yellow-500 mr-1" />
                <span>Reconnecting...</span>
              </>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          {isConnected 
            ? 'Connected to the chat server' 
            : 'Trying to reconnect to the chat server...'}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Typing indicator component
const TypingIndicator = () => {
  const { typingUsers } = useChat();
  
  if (typingUsers.length === 0) return null;
  
  const uniqueTypingUsers = Array.from(new Set(typingUsers.map(u => u.name)));
  const typingText = uniqueTypingUsers.length > 0 
    ? `${uniqueTypingUsers.join(', ')} ${uniqueTypingUsers.length === 1 ? 'is' : 'are'} typing...`
    : '';

  // Get avatars for typing users
  const typingAvatars = typingUsers.slice(0, 3).map((user, index) => (
    <Avatar key={user.id} className="h-6 w-6 border-2 border-background" style={{ zIndex: 10 - index }}>
      <AvatarImage src={user.avatar} alt={user.name} />
      <AvatarFallback className="text-xs">
        {user.name.split(' ').map(n => n[0]).join('')}
      </AvatarFallback>
    </Avatar>
  ));
  
  // Add a +X more indicator if there are more than 3 typing users
  const moreCount = typingUsers.length - 3;
  if (moreCount > 0) {
    typingAvatars.push(
      <div 
        key="more" 
        className="h-6 w-6 rounded-full bg-muted flex items-center justify-center text-xs border-2 border-background"
        style={{ zIndex: 7 }}
      >
        +{moreCount}
      </div>
    );
  }

  return (
    <div className="flex items-center text-xs text-muted-foreground mt-2">
      <div className="flex -space-x-2 mr-2">
        {typingAvatars}
      </div>
      <span className="animate-pulse">
        {typingUsers.length === 1 
          ? `${typingUsers[0].name} is typing...`
          : `${typingUsers.slice(0, 3).map(u => u.name).join(', ')} ${typingUsers.length > 3 ? `and ${moreCount} more` : ''} ${typingUsers.length > 1 ? 'are' : 'is'} typing...`}
      </span>
    </div>
  );
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ className }) => {
  const { 
    messages, 
    typingUsers, 
    isConnected, 
    isLoadingMessages, 
    hasMoreMessages,
    sendMessage,
    editMessage,
    deleteMessage,
    reactToMessage,
    togglePinMessage,
    loadMoreMessages,
    currentUserId,
    reconnect,
    setTyping
  } = useChat();
  
  // Handle retrying a failed message
  const handleRetryMessage = useCallback((messageId: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message) {
      sendMessage(message.content, (message as any).replyTo?.id);
    }
  }, [messages, sendMessage]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [replyingTo, setReplyingTo] = useState<{
    id: string;
    content: string;
    user: { id: string; name: string; avatar?: string };
  } | null>(null);

  // Handle scroll events
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const isNearBottom = scrollHeight - (scrollTop + clientHeight) < 100;
    setIsAtBottom(isNearBottom);
    setShowScrollButton(!isNearBottom);
    
    // Load more messages when scrolling near the top
    if (scrollTop < 100 && hasMoreMessages && !isLoadingMessages) {
      loadMoreMessages();
    }
  }, [hasMoreMessages, isLoadingMessages, loadMoreMessages]);

  // Auto-scroll to bottom when new messages arrive or typing users change
  useEffect(() => {
    if (isAtBottom && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, typingUsers, isAtBottom]);
  
  // Handle sending a message with optional reply
  const handleSendMessage = (content: string, replyToId?: string) => {
    if (!isConnected || !content.trim()) return;
    sendMessage(content, replyToId);
  };
  
  // Handle message actions
  const handleMessageAction = useCallback((action: string, messageId: string, data?: any) => {
    const message = messages.find(m => m.id === messageId);
    if (!message) return;
    
    switch (action) {
      case 'reply':
        // Set the message to reply to in the input
        setReplyingTo({
          id: message.id,
          content: message.content,
          user: message.user
        });
        // Focus the input after a short delay to allow state to update
        setTimeout(() => {
          const input = document.querySelector('textarea');
          input?.focus();
        }, 100);
        break;
        
      case 'edit':
        if (data?.content) {
          editMessage(messageId, data.content);
        }
        break;
        
      case 'delete':
        if (window.confirm('Are you sure you want to delete this message?')) {
          deleteMessage(messageId);
        }
        break;
        
      case 'react':
        if (data?.emoji) {
          reactToMessage(messageId, data.emoji);
        }
        break;
        
      case 'pin':
        togglePinMessage(messageId);
        break;
        
      default:
        console.warn('Unknown message action:', action);
    }
  }, [deleteMessage, editMessage, reactToMessage, togglePinMessage]);

  // Show connection status changes
  useEffect(() => {
    if (!isConnected) {
      toast({
        title: 'Connection lost',
        description: 'Attempting to reconnect...',
        variant: 'destructive',
      });
    } else if (messages.length > 0) {
      toast({
        title: 'Reconnected',
        description: 'Your connection has been restored',
      });
    }
  }, [isConnected, messages.length]);
  
  // Scroll to bottom function
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'auto') => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior });
      if (behavior === 'smooth') {
        setIsAtBottom(true);
        setShowScrollButton(false);
      }
    }
  }, []);

  return (
    <div className="flex flex-col h-full bg-background relative">
      {/* Connection status bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-background/80 backdrop-blur-sm">
        <div className="flex items-center space-x-2">
          <ConnectionStatus />
          {typingUsers.length > 0 && (
            <div className="text-xs text-muted-foreground">
              {typingUsers[0].name} {typingUsers.length > 1 ? `and ${typingUsers.length - 1} others` : ''} typing...
            </div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Users className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>View participants</TooltipContent>
          </Tooltip>
        </div>
      </div>
      
      {/* Messages area */}
      <div className="flex-1 overflow-hidden relative">
        {isLoadingMessages && messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}
        
        {/* Connection lost overlay */}
        {!isConnected && (
          <div className="absolute inset-0 bg-background/90 backdrop-blur-sm flex flex-col items-center justify-center p-4 z-20">
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 max-w-md w-full text-center">
              <div className="flex items-center justify-center mb-3">
                <WifiOff className="h-10 w-10 text-destructive mr-2" />
                <h3 className="text-lg font-semibold">Connection Lost</h3>
              </div>
              <p className="text-muted-foreground mb-4 text-sm">
                We're having trouble connecting to the chat server. Please check your internet connection.
              </p>
              <div className="flex gap-2 justify-center">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={reconnect}
                  className="flex-1 max-w-[200px]"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reconnect
                </Button>
              </div>
            </div>
          </div>
        )}
        
        <ScrollArea 
          ref={scrollAreaRef}
          className="h-full w-full"
          onScroll={handleScroll}
        >
          <div className="flex flex-col-reverse p-4">
            {/* Loading indicator when loading more messages */}
            {isLoadingMessages && (
              <div className="flex justify-center p-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
            
            {/* Messages */}
            <div className="space-y-4">
              <MessageList 
                messages={messages}
                userId={currentUserId}
                onRetry={handleRetryMessage}
                onReply={(messageId) => handleMessageAction('reply', messageId)}
                onEdit={(messageId, content) => handleMessageAction('edit', messageId, { content })}
                onDelete={(messageId) => handleMessageAction('delete', messageId)}
                onReact={(messageId, emoji) => handleMessageAction('react', messageId, { emoji })}
                onPin={(messageId) => handleMessageAction('pin', messageId)}
              />
            </div>
            
            {/* Typing indicator */}
            <div className="pt-2">
              <TypingIndicator />
            </div>
            
            {/* Invisible div at the bottom for auto-scrolling */}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
        
        {/* Chat input */}
        <ChatInput 
          replyTo={replyingTo}
          onCancelReply={() => setReplyingTo(null)}
          className="border-t"
        />
        
        {/* Scroll to bottom button */}
        <AnimatePresence>
          {showScrollButton && (
            <motion.div
              className="absolute right-4 bottom-20 z-10"
              initial={{ opacity: 0, y: 20, scale: 0.9 }}
              animate={{ 
                opacity: 1, 
                y: 0, 
                scale: 1,
                transition: { 
                  type: 'spring',
                  damping: 20,
                  stiffness: 300
                }
              }}
              exit={{ 
                opacity: 0, 
                y: 20, 
                scale: 0.9,
                transition: { duration: 0.2 }
              }}
            >
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => scrollToBottom('smooth')}
                      className="p-2.5 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 hover:shadow-xl transition-all duration-200 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2"
                      aria-label="Scroll to bottom"
                    >
                      <ArrowDown className="h-5 w-5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="left" className="text-xs">
                    New messages
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
