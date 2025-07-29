type MessageHandler = (message: any) => void;
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';
type StateListener = (state: ConnectionState) => void;

class EnhancedWebSocket {
  private static instance: EnhancedWebSocket;
  private socket: WebSocket | null = null;
  private messageListeners: { id: string; handler: MessageHandler }[] = [];
  private stateListeners: { id: string; handler: StateListener }[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private connectionState: ConnectionState = 'disconnected';
  private connectionPromise: Promise<void> | null = null;
  private pendingMessages: any[] = [];
  private pingInterval: NodeJS.Timeout | null = null;
  private lastPong = 0;
  private readonly PING_INTERVAL = 30000;
  private readonly PONG_TIMEOUT = 10000;

  private constructor() {
    this.connect();
  }

  public static getInstance(): EnhancedWebSocket {
    if (!EnhancedWebSocket.instance) {
      EnhancedWebSocket.instance = new EnhancedWebSocket();
    }
    return EnhancedWebSocket.instance;
  }

  private getWebSocketUrl(): string {
    if (process.env.NODE_ENV === 'development') {
      return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    }
    
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return process.env.NEXT_PUBLIC_WS_URL 
        ? process.env.NEXT_PUBLIC_WS_URL.replace(/^https?:/, 'ws:')
        : `${protocol}//${window.location.host}/ws`;
    }
    
    return 'ws://localhost:8000/ws';
  }

  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState === state) return;
    this.connectionState = state;
    this.stateListeners.forEach(({ handler }) => handler(state));
    if (state === 'connected') this.reconnectAttempts = 0;
  }

  public async connect(): Promise<void> {
    if (this.connectionPromise) return this.connectionPromise;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.setConnectionState('error');
      return;
    }

    this.setConnectionState('connecting');
    
    if (this.reconnectAttempts > 0) {
      const delay = Math.min(this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1), 30000);
      await new Promise(resolve => setTimeout(resolve, delay));
      if (this.connectionState === 'connected') return;
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.getWebSocketUrl());
        
        const onOpen = () => {
          console.log('WebSocket connected');
          this.setConnectionState('connected');
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

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'pong') {
          this.lastPong = Date.now();
          return;
        }
        this.messageListeners.forEach(({ handler }) => handler(message));
      } catch (error) {
        console.error('Error handling message:', error);
      }
    };

    this.socket.onclose = () => {
      this.cleanup();
      this.handleReconnect();
    };
  }
  
  private setupPingPong(): void {
    if (this.pingInterval) clearInterval(this.pingInterval);
    this.lastPong = Date.now();
    
    this.pingInterval = setInterval(() => {
      if (this.connectionState !== 'connected' || !this.socket) return;
      
      if (Date.now() - this.lastPong > this.PONG_TIMEOUT + this.PING_INTERVAL) {
        console.warn('No pong received, reconnecting...');
        this.cleanup();
        this.handleReconnect();
        return;
      }
      
      try {
        this.sendInternal({ type: 'ping' });
      } catch (error) {
        console.error('Error sending ping:', error);
      }
    }, this.PING_INTERVAL);
  }

  private cleanup(): void {
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onmessage = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      if (this.socket.readyState === WebSocket.OPEN) this.socket.close();
      this.socket = null;
    }
    this.connectionPromise = null;
    this.setConnectionState('disconnected');
  }

  private handleReconnect(): void {
    this.reconnectAttempts++;
    this.cleanup();
    
    if (this.reconnectAttempts <= this.maxReconnectAttempts) {
      console.log(`Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect();
    } else {
      console.error('Max reconnection attempts reached');
      this.setConnectionState('error');
    }
  }

  private flushPendingMessages(): void {
    if (this.connectionState !== 'connected' || !this.socket) return;
    while (this.pendingMessages.length > 0) {
      const message = this.pendingMessages.shift();
      if (message) this.sendInternal(message);
    }
  }

  private sendInternal(message: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      this.pendingMessages.push(message);
    }
  }

  public send(message: any): void {
    if (this.connectionState !== 'connected') {
      this.pendingMessages.push(message);
      if (this.connectionState === 'disconnected') this.connect();
      return;
    }
    this.sendInternal(message);
  }

  public onMessage(handler: MessageHandler): () => void {
    const id = Math.random().toString(36).substring(2, 11);
    this.messageListeners.push({ id, handler });
    return () => {
      this.messageListeners = this.messageListeners.filter(l => l.id !== id);
    };
  }

  public onStateChange(handler: StateListener): () => void {
    const id = Math.random().toString(36).substring(2, 11);
    this.stateListeners.push({ id, handler });
    handler(this.connectionState);
    return () => {
      this.stateListeners = this.stateListeners.filter(l => l.id !== id);
    };
  }

  public close(): void {
    this.cleanup();
    this.messageListeners = [];
    this.stateListeners = [];
  }
}

export const webSocketService = EnhancedWebSocket.getInstance();
