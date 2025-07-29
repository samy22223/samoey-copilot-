import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Loader2, Paperclip, X, Reply, XCircle } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

type FilePreview = {
  id: string;
  file: File;
  preview: string;
};

// Maximum height for the textarea (in rows)
const MAX_ROWS = 8;

interface ChatInputProps {
  replyTo?: {
    id: string;
    content: string;
    user: { id: string; name: string; avatar?: string };
  } | null;
  onCancelReply?: () => void;
  className?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  replyTo = null, 
  onCancelReply,
  className 
}) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const [files, setFiles] = useState<FilePreview[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const lastTypingTime = useRef(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { sendMessage, setTyping, isConnected, currentUserId } = useChat();
  
  // Cleanup object URLs
  useEffect(() => {
    return () => files.forEach(file => URL.revokeObjectURL(file.preview));
  }, [files]);
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    
    const newFiles = Array.from(e.target.files).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    e.target.value = ''; // Reset file input
  };
  
  const removeFile = (id: string) => {
    setFiles(prev => {
      const fileToRemove = prev.find(f => f.id === id);
      if (fileToRemove) URL.revokeObjectURL(fileToRemove.preview);
      return prev.filter(f => f.id !== id);
    });
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newMessage = e.target.value;
    setMessage(newMessage);
    adjustTextareaHeight();
    
    // Notify other users that we're typing (throttled to avoid spamming)
    const now = Date.now();
    if (now - lastTypingTime.current > 1000) { // Throttle to once per second
      setTyping(true);
      lastTypingTime.current = now;
    }
  };
  
  const handleCompositionStart = () => {
    setIsComposing(true);
  };
  
  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  const handleSubmit = async () => {
    if ((!message.trim() && !files.length) || isComposing || !isConnected) return;
    
    try {
      setIsUploading(true);
      
      // In a real app, upload files here
      // const uploadedFiles = await uploadFiles(files);
      
      // Send message with file references and optional reply
      sendMessage(message, replyTo?.id);
      
      // Reset form
      setMessage('');
      setFiles([]);
      
      // Clear reply if any
      if (replyTo && onCancelReply) {
        onCancelReply();
      }
      
      // Focus the input after sending
      setTimeout(() => textareaRef.current?.focus(), 0);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Show error to user here
    } finally {
      setIsUploading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Only handle Enter key when not composing (e.g., in IME) and not holding Shift
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  const handleBlur = () => {
    // Notify that we've stopped typing when the input loses focus
    setTyping(false);
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  return (
    <div className={cn("border-t bg-background/80 backdrop-blur-sm", className)}>
      {/* Reply preview */}
      {replyTo && (
        <div className="relative bg-muted/50 border-b px-4 py-2 text-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center text-muted-foreground">
              <Reply className="h-3.5 w-3.5 mr-1.5" />
              <span className="font-medium">Replying to {replyTo.user.id === currentUserId ? 'yourself' : replyTo.user.name}</span>
            </div>
            <button 
              onClick={onCancelReply}
              className="p-1 rounded-full hover:bg-muted-foreground/10 text-muted-foreground"
              aria-label="Cancel reply"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="mt-1 text-sm line-clamp-2 text-muted-foreground">
            {replyTo.content.length > 100 
              ? `${replyTo.content.substring(0, 100)}...` 
              : replyTo.content}
          </div>
        </div>
      )}

      {/* File previews */}
      {files.length > 0 && (
        <div className="flex gap-2 p-2 overflow-x-auto border-b">
          {files.map(file => (
            <div key={file.id} className="relative group">
              <div className="h-16 w-16 rounded-md bg-muted overflow-hidden flex-shrink-0">
                {file.file.type.startsWith('image/') ? (
                  <img 
                    src={file.preview} 
                    alt={file.file.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <Paperclip className="h-6 w-6 text-muted-foreground" />
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => removeFile(file.id)}
                className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3" />
              </button>
              <div className="text-xs truncate w-16 mt-1">
                {file.file.name}
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="p-4 flex items-end gap-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-full"
          onClick={() => fileInputRef.current?.click()}
          disabled={!isConnected}
        >
          <Paperclip className="h-4 w-4" />
          <span className="sr-only">Attach file</span>
        </Button>
        
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          multiple
          accept="image/*,.pdf,.doc,.docx,.txt"
        />
        
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleInput}
            onCompositionStart={handleCompositionStart}
            onCompositionEnd={handleCompositionEnd}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={isConnected ? "Type a message..." : "Connecting..."}
            className={cn(
              "min-h-[40px] max-h-[200px] resize-none pr-10 transition-all",
              isFocused && "ring-2 ring-ring ring-offset-2"
            )}
            disabled={!isConnected || isUploading}
            rows={1}
          />
            <span className="sr-only">Attach file</span>
          </Button>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            multiple
            accept="image/*,.pdf,.doc,.docx,.txt"
          />
          
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={handleInput}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={isConnected ? "Type a message..." : "Connecting..."}
              className={cn(
                "min-h-[40px] max-h-[200px] resize-none pr-10 transition-all",
                isFocused && "ring-2 ring-ring ring-offset-2"
              )}
              disabled={!isConnected || isUploading}
              rows={1}
            />
          </div>
          
          <Button 
            type="button"
            onClick={handleSubmit} 
            size="icon" 
            className="h-9 w-9 rounded-full flex-shrink-0"
            disabled={(!message.trim() && !files.length) || isComposing || !isConnected}
          >
            {isUploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span className="sr-only">Send message</span>
          </Button>
        </div>
          disabled={(!message.trim() && !files.length) || isComposing || !isConnected}
        >
          {isUploading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          <span className="sr-only">Send message</span>
        </Button>
      </div>
    </div>
  );
};
