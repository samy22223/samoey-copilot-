import React, { useMemo, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Message as MessageType } from '@/types/chat';
import { Message, ExtendedMessage } from './Message';
import { useChat } from '@/contexts/ChatContext';

interface MessageListProps {
  messages: ExtendedMessage[];
  userId?: string;
  onRetry?: (messageId: string) => void;
  onReply?: (messageId: string) => void;
  onEdit?: (messageId: string, content: string) => void;
  onDelete?: (messageId: string) => void;
  onReact?: (messageId: string, emoji: string) => void;
  onPin?: (messageId: string) => void;
  className?: string;
}

export const MessageList = React.forwardRef<HTMLDivElement, MessageListProps>(
  ({
    messages,
    userId,
    onRetry,
    onReply,
    onEdit,
    onDelete,
    onReact,
    onPin,
    className,
  }, ref) => {
    // Group consecutive messages from the same user
    const groupedMessages = useMemo(() => {
      const groups: { messages: MessageType[]; userId: string }[] = [];
      
      messages.forEach((message) => {
        const lastGroup = groups[groups.length - 1];
        
        if (lastGroup && lastGroup.userId === message.userId) {
          lastGroup.messages.push(message);
        } else {
          groups.push({
            messages: [message],
            userId: message.userId,
          });
        }
      });
      
      return groups;
    }, [messages]);

    if (messages.length === 0) {
      return (
        <div className={cn("flex flex-col items-center justify-center h-full text-muted-foreground", className)}>
          <p>No messages yet</p>
        </div>
      );
    }

    return (
      <div ref={ref} className={cn("flex flex-col-reverse overflow-y-auto", className)}>
        {groupedMessages.map((group, groupIndex) => {
          const isCurrentUser = group.userId === userId;
          const isLastGroup = groupIndex === 0; // Since we're in reverse order
          
          return (
            <div 
              key={group.messages[0].id || group.messages[0].tempId}
              className={cn(
                "space-y-1 px-2 py-1",
                isLastGroup && "pt-2"
              )}
            >
              {group.messages.map((message, messageIndex) => {
                const isLastInGroup = messageIndex === group.messages.length - 1;
                
                return (
                  <Message
                    key={message.id || message.tempId}
                    message={message}
                    isCurrentUser={isCurrentUser}
                    onRetry={onRetry}
                    onReply={onReply}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onReact={onReact}
                    onPin={onPin}
                    className={cn(
                      !isLastInGroup && 'pb-0',
                      messageIndex > 0 && 'pt-1',
                      message.isPinned && 'bg-yellow-50 dark:bg-yellow-900/20'
                    )}
                  />
                );
              })}
            </div>
          );
        })}
      </div>
    );
  }
);

MessageList.displayName = 'MessageList';
