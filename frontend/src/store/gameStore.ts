import { create } from 'zustand';
import { api } from '../api/client';
import type { AIDifficulty, GameState } from '../api/types';
import { sounds, ensureAudioReady } from '../hooks/useSound';
import { useSoundStore } from './soundStore';

function playSound(name: keyof typeof sounds) {
  if (useSoundStore.getState().enabled) {
    ensureAudioReady();
    sounds[name]();
  }
}

const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

interface GameStore {
  game: GameState | null;
  loading: boolean;
  error: string | null;
  selectedIndices: number[];
  difficulty: AIDifficulty;

  setDifficulty: (d: AIDifficulty) => void;
  toggleSelect: (idx: number) => void;
  clearSelection: () => void;

  newGame: (playerName: string) => Promise<void>;
  discard: () => Promise<void>;
  playCard: (idx: number) => Promise<void>;
  sayGo: () => Promise<void>;
  acknowledge: () => Promise<void>;
}

export const useGameStore = create<GameStore>((set, get) => ({
  game: null,
  loading: false,
  error: null,
  selectedIndices: [],
  difficulty: 'easy',

  setDifficulty: (d) => set({ difficulty: d }),

  toggleSelect: (idx) => {
    playSound('tap');
    set((s) => {
      const sel = s.selectedIndices.includes(idx)
        ? s.selectedIndices.filter((i) => i !== idx)
        : [...s.selectedIndices, idx];
      return { selectedIndices: sel };
    });
  },

  clearSelection: () => set({ selectedIndices: [] }),

  newGame: async (playerName) => {
    set({ loading: true, error: null, selectedIndices: [] });
    try {
      const game = await api.newGame(playerName, get().difficulty);
      playSound('shuffle');
      set({ game, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  discard: async () => {
    const { game, selectedIndices } = get();
    if (!game || selectedIndices.length !== 2) return;
    set({ loading: true, error: null });
    try {
      const updated = await api.discard(game.game_id, selectedIndices);
      playSound('shuffle');
      set({ game: updated, loading: false, selectedIndices: [] });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  playCard: async (idx) => {
    const { game } = get();
    if (!game) return;
    set({ loading: true, error: null });
    try {
      const updated = await api.playCard(game.game_id, idx);
      const computerActed = updated.last_action?.actor === game.opponent.name;

      if (computerActed) {
        // Show player's move immediately
        const playerCard = game.player.hand[idx];
        playSound('cardPlay');
        const intermediate: GameState = {
          ...game,
          player: {
            ...game.player,
            hand: game.player.hand.filter((_, i) => i !== idx),
          },
          play_pile: [...game.play_pile, playerCard],
          running_total: game.running_total + playerCard.value,
          last_action: {
            actor: game.player.name,
            action: 'play',
            card: playerCard,
            score_events: [],
            message: `${game.player.name} played ${playerCard.rank}`,
          },
        };
        set({ game: intermediate, loading: false });

        // Computer "thinks"
        await delay(800 + Math.random() * 400);

        // Reveal computer's move
        playSound('cardPlay');
        set({ game: updated });
      } else {
        playSound('cardPlay');
        set({ game: updated, loading: false });
      }

      // Play score sounds
      const events = updated.last_action?.score_events ?? [];
      if (events.some((e) => e.reason.includes('15'))) playSound('fifteen');
      else if (events.some((e) => e.reason.includes('31'))) playSound('thirtyOne');
      else if (events.reduce((s, e) => s + e.points, 0) > 0) playSound('score');
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  sayGo: async () => {
    const { game } = get();
    if (!game) return;
    set({ loading: true, error: null });
    try {
      playSound('go');
      const updated = await api.sayGo(game.game_id);

      // If computer responded, add thinking delay
      if (updated.last_action?.actor === game.opponent.name) {
        await delay(600 + Math.random() * 400);
        playSound('cardPlay');
      }

      set({ game: updated, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  acknowledge: async () => {
    const { game } = get();
    if (!game) return;
    set({ loading: true, error: null });
    try {
      const updated = await api.acknowledge(game.game_id);
      await delay(300);
      playSound('score');
      set({ game: updated, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },
}));
