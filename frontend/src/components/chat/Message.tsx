import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Message as MessageType } from '@/types/chat';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';
import { 
  Check, 
  Clock, 
  AlertCircle, 
  Loader2, 
  MoreVertical, 
  Reply, 
  Edit, 
  Trash2, 
  Pin, 
  ThumbsUp, 
  SmilePlus,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { EmojiPicker } from './EmojiPicker';
import { formatDistanceToNow } from 'date-fns';
import { RefreshCw } from 'lucide-react';

interface MessageStatusProps {
  status: MessageType['status'];
  timestamp: string;
  showTime?: boolean;
}

interface ExtendedMessage extends MessageType {
  isPinned?: boolean;
  replyTo?: {
    id: string;
    content: string;
    user?: {
      id: string;
      name: string;
      avatar?: string;
    };
  };
  reactions?: Record<string, string[]>;
};

const MessageStatus: React.FC<MessageStatusProps> = ({ status, timestamp, showTime = true }) => {
  const [formattedTime, tooltip] = React.useMemo(() => {
    const date = new Date(timestamp);
    return [
      formatDistanceToNow(date, { addSuffix: true }),
      new Date(timestamp).toLocaleString()
    ];
  }, [timestamp]);

  const statusIcon = React.useMemo(() => {
    switch (status) {
      case 'sending':
        return <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />;
      case 'sent':
        return <Check className="h-3 w-3 text-muted-foreground" />;
      case 'delivered':
        return (
          <div className="flex">
            <Check className="h-3 w-3 text-muted-foreground" />
            <Check className="h-3 w-3 -ml-1 text-muted-foreground" />
          </div>
        );
      case 'read':
        return (
          <div className="flex text-blue-500">
            <Check className="h-3 w-3" />
            <Check className="h-3 w-3 -ml-1" />
          </div>
        );
      case 'failed':
        return <AlertCircle className="h-3 w-3 text-destructive" />;
      default:
        return <Clock className="h-3 w-3 text-muted-foreground" />;
    }
  }, [status]);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center space-x-1">
            {showTime && <span className="text-xs text-muted-foreground">{formattedTime}</span>}
            {statusIcon}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltip}</p>
          <p className="text-muted-foreground capitalize">{status}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

interface MessageProps {
  message: ExtendedMessage;
  isCurrentUser: boolean;
  onReply?: (messageId: string) => void;
  onEdit?: (messageId: string, content: string) => void;
  onDelete?: (messageId: string) => void;
  onReact?: (messageId: string, emoji: string) => void;
  onPin?: (messageId: string) => void;
  onRetry?: (messageId: string) => void;
  className?: string;
}

export const Message: React.FC<MessageProps> = ({
  message,
  isCurrentUser,
  onReply,
  onEdit,
  onDelete,
  onReact,
  onPin,
  onRetry,
  className,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(message.content);
  const editInputRef = useRef<HTMLTextAreaElement>(null);
  const [showReactions, setShowReactions] = useState(false);

  const handleEdit = useCallback(() => {
    if (editedContent.trim() && editedContent !== message.content) {
      onEdit?.(message.id, editedContent);
    }
    setIsEditing(false);
  }, [editedContent, message.content, message.id, onEdit]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleEdit();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditedContent(message.content);
    }
  }, [handleEdit, message.content]);

  const handleReaction = useCallback((emoji: string) => {
    onReact?.(message.id, emoji);
    setShowReactions(false);
  }, [message.id, onReact]);

  // Auto-resize textarea when editing
  useEffect(() => {
    if (isEditing && editInputRef.current) {
      editInputRef.current.style.height = 'auto';
      editInputRef.current.style.height = `${editInputRef.current.scrollHeight}px`;
    }
  }, [isEditing, editedContent]);

  // Common reactions to show in the quick picker
  const commonReactions = ['👍', '❤️', '😂', '😮', '😢', '🙏'];

  return (
    <div 
      className={cn(
        'group flex items-start gap-2 p-2 rounded-lg transition-colors',
        isCurrentUser ? 'justify-end' : 'justify-start',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {!isCurrentUser && (
        <Avatar className="h-8 w-8 mt-1 flex-shrink-0">
          <AvatarImage src={message.user?.avatar} alt={message.user?.name} />
          <AvatarFallback>
            {message.user?.name?.substring(0, 2).toUpperCase() || 'U'}
          </AvatarFallback>
        </Avatar>
      )}

      <div className="flex-1 max-w-[80%] flex flex-col">
        {!isCurrentUser && (
          <div className="text-sm font-medium mb-1">
            {message.user?.name || 'Unknown User'}
          </div>
        )}
        
        <div className={cn(
          'relative rounded-lg p-3',
          isCurrentUser 
            ? 'bg-primary text-primary-foreground rounded-tr-none' 
            : 'bg-muted rounded-tl-none',
          message.status === 'failed' && 'border border-destructive/50',
          isHovered && 'shadow-sm',
          message.isPinned && 'ring-2 ring-yellow-400/50'
        )}>
          {/* Reply preview */}
          {message.replyTo && (
            <div className="text-xs bg-black/10 dark:bg-white/10 rounded p-2 mb-2 border-l-2 border-blue-500">
              <div className="font-medium truncate">
                {message.replyTo.user?.name || 'Unknown User'}
              </div>
              <div className="truncate text-muted-foreground">
                {message.replyTo.content}
              </div>
            </div>
          )}
          
          {/* Message content */}
          {isEditing ? (
            <div className="relative">
              <textarea
                ref={editInputRef}
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleEdit}
                className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-foreground resize-none"
                autoFocus
                rows={Math.min(5, editedContent.split('\n').length + 1)}
              />
              <div className="text-xs text-muted-foreground mt-1">
                Press Enter to save, Esc to cancel
              </div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              
              {/* Message reactions */}
              {message.reactions && Object.keys(message.reactions).length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {Object.entries(message.reactions).map(([emoji, users]) => (
                    <button
                      key={emoji}
                      onClick={() => onReact?.(message.id, emoji)}
                      className={cn(
                        'text-xs px-2 py-0.5 rounded-full bg-black/10 dark:bg-white/10',
                        'hover:bg-black/20 dark:hover:bg-white/20 transition-colors',
                        'flex items-center gap-1'
                      )}
                    >
                      <span>{emoji}</span>
                      <span>{users.length}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* Quick reactions */}
          {(isHovered || showReactions) && onReact && (
            <div className="absolute -bottom-2 right-0 flex items-center gap-1 bg-background rounded-full shadow-md border p-0.5">
              {commonReactions.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => handleReaction(emoji)}
                  className="text-lg hover:scale-125 transform transition-transform p-1"
                >
                  {emoji}
                </button>
              ))}
              <EmojiPicker onSelect={handleReaction}>
                <button className="text-muted-foreground hover:text-foreground p-1">
                  <SmilePlus className="h-4 w-4" />
                </button>
              </EmojiPicker>
            </div>
          )}
          
          {/* Message actions */}
          <div className={cn(
            'absolute -right-2 -top-2 flex items-center gap-1 bg-background rounded-full shadow-sm border',
            'opacity-0 group-hover:opacity-100 transition-opacity',
            isHovered && 'opacity-100',
            isCurrentUser ? 'flex-row' : 'flex-row-reverse left-auto right-0'
          )}>
            <EmojiPicker onSelect={handleReaction}>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 rounded-full p-0 hover:bg-muted"
                onClick={(e) => e.stopPropagation()}
              >
                <SmilePlus className="h-3.5 w-3.5" />
              </Button>
            </EmojiPicker>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 rounded-full p-0 hover:bg-muted"
                >
                  <MoreVertical className="h-3.5 w-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                {onReply && (
                  <DropdownMenuItem onClick={() => onReply(message.id)}>
                    <Reply className="mr-2 h-4 w-4" />
                    <span>Reply</span>
                  </DropdownMenuItem>
                )}
                {onEdit && isCurrentUser && (
                  <DropdownMenuItem onSelect={() => setIsEditing(true)}>
                    <Edit className="mr-2 h-4 w-4" />
                    <span>Edit</span>
                  </DropdownMenuItem>
                )}
                {onDelete && isCurrentUser && (
                  <DropdownMenuItem 
                    className="text-destructive focus:text-destructive"
                    onSelect={() => onDelete(message.id)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    <span>Delete</span>
                  </DropdownMenuItem>
                )}
                {onPin && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onSelect={() => onPin(message.id)}>
                      <Pin className="mr-2 h-4 w-4" />
                      <span>{message.isPinned ? 'Unpin' : 'Pin'}</span>
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          
          {/* Status and timestamp */}
          <div className="mt-1 flex items-center justify-end gap-2">
            {message.status === 'failed' && onRetry && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5 text-destructive hover:bg-destructive/10"
                      onClick={() => onRetry(message.id)}
                    >
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Retry sending</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            <MessageStatus 
              status={message.status} 
              timestamp={message.timestamp} 
              showTime={isHovered}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
