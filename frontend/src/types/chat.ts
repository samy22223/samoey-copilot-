export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'read' | 'failed';

export interface User {
  id: string;
  name: string;
  avatar?: string;
  email?: string;
  status?: 'online' | 'offline' | 'away';
}

export interface Message {
  id: string;
  content: string;
  userId: string;
  user: User;
  timestamp: string;
  status?: MessageStatus;
  tempId?: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  title: string;
  participants: User[];
  lastMessage?: Message;
  unreadCount: number;
  createdAt: string;
  updatedAt: string;
  isGroup: boolean;
}

export interface TypingUser {
  userId: string;
  name: string;
  lastTypingTime: number;
  avatar?: string;
}

export interface ChatContextType {
  messages: Message[];
  sendMessage: (content: string) => void;
  isTyping: boolean;
  setTyping: (isTyping: boolean) => void;
  typingUsers: TypingUser[];
  isConnected: boolean;
  currentConversation?: Conversation | null;
  setCurrentConversation: (conversation: Conversation | null) => void;
  conversations: Conversation[];
  loadMoreMessages: () => Promise<void>;
  hasMoreMessages: boolean;
  isLoadingMessages: boolean;
}
