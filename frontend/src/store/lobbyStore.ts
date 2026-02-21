import { create } from 'zustand';
import { GameWebSocket } from '../api/websocket';
import type { GameState } from '../api/types';

type LobbyStatus = 'idle' | 'connecting' | 'waiting' | 'in_game';

interface LobbyStore {
  status: LobbyStatus;
  joinCode: string | null;
  error: string | null;
  gameState: GameState | null;
  ws: GameWebSocket | null;

  quickMatch: (name: string) => void;
  createPrivate: (name: string) => void;
  joinPrivate: (name: string, code: string) => void;
  sendDiscard: (cardIndices: number[]) => void;
  sendPlay: (cardIndex: number) => void;
  sendGo: () => void;
  sendAcknowledge: () => void;
  sendChat: (message: string) => void;
  disconnect: () => void;
}

export const useLobbyStore = create<LobbyStore>((set, get) => {
  const setupWs = (): GameWebSocket => {
    const ws = new GameWebSocket();

    ws.on('connected', () => set({ status: 'waiting' }));
    ws.on('disconnected', () => {
      const { status } = get();
      if (status !== 'idle') set({ error: 'Connection lost' });
    });
    ws.on('waiting', () => set({ status: 'waiting' }));
    ws.on('private_created', (data: any) => set({ joinCode: data.code }));
    ws.on('game_start', (data: any) => set({ status: 'in_game', gameState: data.state }));
    ws.on('game_state', (data: any) => set({ gameState: data.state }));
    ws.on('error', (data: any) => set({ error: data.message }));

    ws.connect();
    return ws;
  };

  return {
    status: 'idle',
    joinCode: null,
    error: null,
    gameState: null,
    ws: null,

    quickMatch: (name) => {
      const ws = setupWs();
      set({ ws, status: 'connecting', error: null, joinCode: null });
      ws.on('connected', () => ws.send({ type: 'quick_match', name }));
    },

    createPrivate: (name) => {
      const ws = setupWs();
      set({ ws, status: 'connecting', error: null, joinCode: null });
      ws.on('connected', () => ws.send({ type: 'create_private', name }));
    },

    joinPrivate: (name, code) => {
      const ws = setupWs();
      set({ ws, status: 'connecting', error: null, joinCode: null });
      ws.on('connected', () => ws.send({ type: 'join_private', name, code }));
    },

    sendDiscard: (cardIndices) => get().ws?.send({ type: 'discard', card_indices: cardIndices }),
    sendPlay: (cardIndex) => get().ws?.send({ type: 'play_card', card_index: cardIndex }),
    sendGo: () => get().ws?.send({ type: 'say_go' }),
    sendAcknowledge: () => get().ws?.send({ type: 'acknowledge' }),
    sendChat: (message) => get().ws?.send({ type: 'chat', message }),

    disconnect: () => {
      get().ws?.disconnect();
      set({ ws: null, status: 'idle', joinCode: null, error: null, gameState: null });
    },
  };
});
