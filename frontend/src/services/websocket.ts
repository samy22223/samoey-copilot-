import { v4 as uuidv4 } from 'uuid';
import { Message } from './api';

type MessageCallback = (message: Message) => void;
type ErrorCallback = (error: Event) => void;

export type MessageHandler = (message: any) => void;

export private messageListeners: { id: string; handler: MessageHandler }[] = [];

type WebSocketMessage = {
  type: string;
  [key: string]: any;
};

class WebSocketService {
  private static instance: WebSocketService;
  private socket: WebSocket | null = null;
  private callbacks = new Map<string, MessageCallback>();
  private errorHandlers = new Set<ErrorCallback>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000; // 3 seconds
  private isConnected = false;
  private connectionPromise: Promise<void> | null = null;
  private pendingMessages: WebSocketMessage[] = [];
  private pingInterval: NodeJS.Timeout | null = null;

  private constructor() {
    this.connect();
  }

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  private getWebSocketUrl(): string {
    // In development, use the environment variable or default to localhost
    if (process.env.NODE_ENV === 'development') {
      return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    }
    
    // In production, use the environment variable or derive from window.location
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.NEXT_PUBLIC_WS_URL 
        ? process.env.NEXT_PUBLIC_WS_URL.replace(/^https?:/, 'ws:')
        : `${protocol}//${window.location.host}/ws`;
      
      return host;
    }
    
    // Fallback for SSR
    return 'ws://localhost:8000/ws';
  }

  private async connect(): Promise<void> {
    // If already connected or connecting, return the existing promise
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    // Don't try to connect if we've exceeded max attempts
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      const wsUrl = this.getWebSocketUrl();
      console.log(`Connecting to WebSocket at ${wsUrl}`);
      
      try {
        this.socket = new WebSocket(wsUrl);
        
        const onOpen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.setupPingPong();
          this.flushPendingMessages();
          resolve();
        };
        
        const onError = (error: Event) => {
          console.error('WebSocket error:', error);
          this.cleanup();
          reject(error);
          this.handleReconnect();
        };
        
        this.socket.addEventListener('open', onOpen, { once: true });
        this.socket.addEventListener('error', onError, { once: true });
        
        this.setupEventListeners();
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        this.cleanup();
        reject(error);
        this.handleReconnect();
      }
    });
    
    return this.connectionPromise;
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      console.log('WebSocket connected');
    };

    this.socket.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        this.callbacks.forEach(callback => callback(message));
      } catch (error) {
        console.error('Error processing message:', error);
      }
    };

    this.socket.onclose = () => {
      this.isConnected = false;
      this.handleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.errorHandlers.forEach(handler => handler(error));
    };
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => this.connect(), delay);
  }

  public send(message: any): void {
    if (!this.isConnected || !this.socket) {
      console.warn('WebSocket not connected');
      return;
    }
    
    try {
      const messageString = typeof message === 'string' ? message : JSON.stringify(message);
      this.socket.send(messageString);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }

  public onMessage(callback: MessageCallback): string {
    const id = uuidv4();
    this.callbacks.set(id, callback);
    return id;
  }

  public offMessage(callbackId: string): void {
    this.callbacks.delete(callbackId);
  }

  public onError(callback: ErrorCallback): () => void {
    this.errorHandlers.add(callback);
    return () => this.errorHandlers.delete(callback);
  }

  public close(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
    }
  }
}

export const webSocketService = WebSocketService.getInstance();
