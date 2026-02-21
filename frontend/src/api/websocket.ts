type MessageHandler = (data: any) => void;

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnects = 5;
  private shouldReconnect = true;

  constructor(url?: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = url || `${protocol}//${window.location.host}/ws`;
  }

  connect(): void {
    this.shouldReconnect = true;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.emit('connected', {});
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit(data.type, data);
      } catch {}
    };

    this.ws.onclose = () => {
      this.emit('disconnected', {});
      if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnects) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        setTimeout(() => this.connect(), delay);
      }
    };

    this.ws.onerror = () => {};
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.ws?.close();
    this.ws = null;
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(type: string, handler: MessageHandler): void {
    const list = this.handlers.get(type) || [];
    list.push(handler);
    this.handlers.set(type, list);
  }

  off(type: string, handler: MessageHandler): void {
    const list = this.handlers.get(type) || [];
    this.handlers.set(type, list.filter((h) => h !== handler));
  }

  private emit(type: string, data: any): void {
    const list = this.handlers.get(type) || [];
    list.forEach((h) => h(data));
  }
}
