'use client';

import { useEffect, useState } from 'react';
import { webSocketService } from '@/services/websocket';

export default function WsTestPage() {
  const [status, setStatus] = useState('Connecting...');
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    // Handle incoming messages
    const messageHandler = (message: any) => {
      setMessages(prev => [...prev, JSON.stringify(message, null, 2)]);
    };

    // Handle errors
    const errorHandler = (error: Event) => {
      console.error('WebSocket error:', error);
      setStatus(`Error: ${error.type}`);
    };

    // Subscribe to messages
    const messageId = webSocketService.onMessage(messageHandler);
    const removeErrorHandler = webSocketService.onError(errorHandler);

    // Send a test message
    webSocketService.send({ type: 'test', data: 'Hello from client' });

    // Update status when connected
    setStatus('Connected to WebSocket');

    // Clean up
    return () => {
      webSocketService.offMessage(messageId);
      removeErrorHandler();
    };
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">WebSocket Test</h1>
      
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <p className="font-medium">Status: <span className="text-blue-600">{status}</span></p>
      </div>
      
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Messages</h2>
        {messages.length === 0 ? (
          <p className="text-gray-500">No messages received yet</p>
        ) : (
          <div className="space-y-2">
            {messages.map((msg, index) => (
              <pre key={index} className="p-3 bg-gray-800 text-green-400 rounded-md overflow-x-auto text-sm">
                {msg}
              </pre>
            ))}
          </div>
        )}
      </div>
      
      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="font-medium text-yellow-800 mb-2">Troubleshooting</h3>
        <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
          <li>Make sure the backend server is running</li>
          <li>Check the browser console for any errors</li>
          <li>Verify the WebSocket URL in <code className="bg-yellow-100 px-1 rounded">.env.local</code></li>
          <li>Check if there are any CORS issues in the browser's network tab</li>
        </ul>
      </div>
    </div>
  );
}
