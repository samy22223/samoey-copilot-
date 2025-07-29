'use client';

import { ChatProvider } from '@/contexts/ChatContext';
import { ChatInterface } from '@/components/chat/ChatInterface';

export default function ChatPage() {
  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col h-full">
        <ChatProvider>
          <ChatInterface />
        </ChatProvider>
      </div>
    </div>
  );
}
