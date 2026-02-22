import { create } from 'zustand';
import { GameWebSocket } from '../api/websocket';
import type { GameState } from '../api/types';
import { useStatsStore } from './statsStore';

type LobbyStatus = 'idle' | 'connecting' | 'waiting' | 'in_game';

export interface ChatMessage {
  from: 'me' | 'opponent';
  text: string;
  ts: number;
}

interface LobbyStore {
  status: LobbyStatus;
  joinCode: string | null;
  error: string | null;
  gameState: GameState | null;
  chatMessages: ChatMessage[];
  ws: GameWebSocket | null;
  statsRecorded: boolean;

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
    ws.on('game_state', (data: any) => {
      const state = data.state as GameState;
      set({ gameState: state });
      // Record stats once when game ends
      if (state.winner && !get().statsRecorded) {
        set({ statsRecorded: true });
        const stats = state.game_stats;
        useStatsStore.getState().recordGame({
          player_name: state.player.name,
          opponent_name: state.opponent.name,
          player_score: state.player.score,
          opponent_score: state.opponent.score,
          won: state.winner === state.player.name,
          game_mode: 'multiplayer',
          hand_scores: stats?.hand_scores ?? [],
          crib_scores: stats?.crib_scores ?? [],
          highest_hand_score: stats?.highest_hand_score ?? 0,
          total_points_scored: stats?.total_points_scored ?? state.player.score,
        });
      }
    });
    ws.on('opponent_disconnected', (data: any) => set({ error: data.message }));
    ws.on('chat', (data: any) => {
      const msg: ChatMessage = { from: 'opponent', text: data.message, ts: Date.now() };
      set((s) => ({ chatMessages: [...s.chatMessages, msg] }));
    });
    ws.on('error', (data: any) => set({ error: data.message }));

    ws.connect();
    return ws;
  };

  return {
    status: 'idle',
    joinCode: null,
    error: null,
    gameState: null,
    chatMessages: [],
    ws: null,
    statsRecorded: false,

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
    sendChat: (message) => {
      get().ws?.send({ type: 'chat', message });
      const msg: ChatMessage = { from: 'me', text: message, ts: Date.now() };
      set((s) => ({ chatMessages: [...s.chatMessages, msg] }));
    },

    disconnect: () => {
      get().ws?.disconnect();
      set({ ws: null, status: 'idle', joinCode: null, error: null, gameState: null, chatMessages: [], statsRecorded: false });
    },
  };
});
