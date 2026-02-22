import { create } from 'zustand';
import { api } from '../api/client';
import type { AIDifficulty, GameState, LastAction } from '../api/types';
import { sounds, ensureAudioReady } from '../hooks/useSound';
import { useSoundStore } from './soundStore';

function playSound(name: keyof typeof sounds) {
  if (useSoundStore.getState().enabled) {
    ensureAudioReady();
    sounds[name]();
  }
}

function playScoreSound(action: LastAction | undefined) {
  if (!action) return;
  const events = action.score_events ?? [];
  if (events.some((e) => e.reason.includes('15'))) playSound('fifteen');
  else if (events.some((e) => e.reason.includes('31'))) playSound('thirtyOne');
  else if (events.reduce((s, e) => s + e.points, 0) > 0) playSound('score');
}

function playGameOverSound(state: GameState) {
  if (!state.winner) return;
  playSound(state.winner === state.player.name ? 'win' : 'lose');
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
      const log = updated.action_log ?? [];
      const computerPlays = log.filter(
        (a) => a.actor === updated.opponent.name && a.action === 'play',
      );

      if (computerPlays.length === 0) {
        set({ game: updated, loading: false, selectedIndices: [] });
        playGameOverSound(updated);
        return;
      }

      // Show the phase transition first (play phase starts)
      set({
        game: {
          ...updated,
          play_pile: [],
          running_total: 0,
          last_action: undefined,
          action_log: [],
        },
        loading: false,
        selectedIndices: [],
      });

      // Step through computer's opening plays
      let playPile: typeof updated.play_pile = [];
      let runTotal = 0;
      let oppCount = updated.opponent.hand_count + computerPlays.length;
      let oppScore = updated.opponent.score;

      for (let i = 0; i < log.length; i++) {
        await delay(800 + Math.random() * 400);
        const action = log[i];
        const isLast = i === log.length - 1;

        let displayPile = playPile;
        let displayTotal = runTotal;

        if (action.action === 'play' && action.card) {
          playSound('cardPlay');
          displayPile = [...playPile, action.card];
          displayTotal = runTotal + action.card.value;
          oppCount--;
          const pts = action.score_events.reduce((s, e) => s + e.points, 0);
          oppScore += pts;
        }

        playScoreSound(action);

        if (isLast) {
          set({ game: updated });
          playGameOverSound(updated);
        } else {
          set({
            game: {
              ...get().game!,
              play_pile: displayPile,
              running_total: displayTotal,
              opponent: { ...updated.opponent, hand_count: oppCount, score: oppScore },
              last_action: action,
              action_log: log.slice(0, i + 1),
            },
          });
        }

        // Update tracking for next iteration
        if (action.action === 'play' && action.card) {
          playPile = displayPile;
          runTotal = displayTotal;
          if (runTotal >= 31) {
            playPile = [];
            runTotal = 0;
          }
        }
      }
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
      const log = updated.action_log ?? [];
      const computerActions = log.filter(
        (a) => a.actor === game.opponent.name && a.action === 'play',
      );

      if (computerActions.length === 0) {
        // No computer play — just show player's card
        playSound('cardPlay');
        playScoreSound(log[0]);
        set({ game: updated, loading: false });
        playGameOverSound(updated);
        return;
      }

      // Step 1: Show player's card immediately
      const playerCard = game.player.hand[idx];
      const playerHand = game.player.hand.filter((_, i) => i !== idx);
      playSound('cardPlay');
      let playPile = [...game.play_pile, playerCard];
      let runTotal = game.running_total + playerCard.value;
      let oppCount = game.opponent.hand_count;
      let playerScore = game.player.score;
      let oppScore = game.opponent.score;

      // Apply player score events
      const playerAction = log[0];
      if (playerAction) {
        const pts = playerAction.score_events.reduce((s, e) => s + e.points, 0);
        if (playerAction.actor === game.player.name) playerScore += pts;
        playScoreSound(playerAction);
      }

      set({
        game: {
          ...game,
          player: { ...game.player, hand: playerHand, score: playerScore },
          opponent: { ...game.opponent, score: oppScore },
          play_pile: playPile,
          running_total: runTotal,
          last_action: playerAction,
          action_log: [playerAction],
        },
        loading: false,
      });

      // Reset pile after showing the card (for next iteration tracking)
      if (runTotal >= 31) {
        playPile = [];
        runTotal = 0;
      }

      // Step 2+: Show each subsequent action with delay
      for (let i = 1; i < log.length; i++) {
        await delay(800 + Math.random() * 400);
        const action = log[i];
        const isLast = i === log.length - 1;

        // Build display state for this step
        let displayPile = playPile;
        let displayTotal = runTotal;

        if (action.action === 'play' && action.card) {
          playSound('cardPlay');
          displayPile = [...playPile, action.card];
          displayTotal = runTotal + action.card.value;
          if (action.actor === game.opponent.name) oppCount--;
          const pts = action.score_events.reduce((s, e) => s + e.points, 0);
          if (action.actor === game.opponent.name) oppScore += pts;
          else playerScore += pts;
        } else if (action.action === 'go') {
          playSound('go');
        } else if (action.action === 'score') {
          const pts = action.score_events.reduce((s, e) => s + e.points, 0);
          if (action.actor === game.opponent.name) oppScore += pts;
          else playerScore += pts;
        }

        playScoreSound(action);

        if (isLast) {
          // Use server's authoritative final state
          set({ game: updated });
          playGameOverSound(updated);
        } else {
          set({
            game: {
              ...get().game!,
              play_pile: displayPile,
              running_total: displayTotal,
              player: { ...game.player, hand: playerHand, score: playerScore },
              opponent: { ...game.opponent, hand_count: oppCount, score: oppScore },
              last_action: action,
              action_log: log.slice(0, i + 1),
            },
          });
        }

        // Update tracking for next iteration
        if (action.action === 'play' && action.card) {
          playPile = displayPile;
          runTotal = displayTotal;
          if (runTotal >= 31) {
            playPile = [];
            runTotal = 0;
          }
        }
      }
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
      const log = updated.action_log ?? [];
      const computerPlays = log.filter(
        (a) => a.actor === game.opponent.name && a.action === 'play',
      );

      if (computerPlays.length === 0) {
        // No computer card plays — just show final state
        set({ game: updated, loading: false });
        playGameOverSound(updated);
        return;
      }

      // Show human's Go immediately
      set({
        game: {
          ...game,
          last_action: log[0],
          action_log: [log[0]],
        },
        loading: false,
      });

      // Step through subsequent actions with delays
      let playPile = [...game.play_pile];
      let runTotal = game.running_total;
      let oppCount = game.opponent.hand_count;
      let oppScore = game.opponent.score;
      let playerScore = game.player.score;

      for (let i = 1; i < log.length; i++) {
        await delay(800 + Math.random() * 400);
        const action = log[i];
        const isLast = i === log.length - 1;

        let displayPile = playPile;
        let displayTotal = runTotal;

        if (action.action === 'play' && action.card) {
          playSound('cardPlay');
          displayPile = [...playPile, action.card];
          displayTotal = runTotal + action.card.value;
          if (action.actor === game.opponent.name) oppCount--;
          const pts = action.score_events.reduce((s, e) => s + e.points, 0);
          if (action.actor === game.opponent.name) oppScore += pts;
          else playerScore += pts;
        } else if (action.action === 'go') {
          playSound('go');
        } else if (action.action === 'score') {
          const pts = action.score_events.reduce((s, e) => s + e.points, 0);
          if (action.actor === game.opponent.name) oppScore += pts;
          else playerScore += pts;
        }

        playScoreSound(action);

        if (isLast) {
          set({ game: updated });
          playGameOverSound(updated);
        } else {
          set({
            game: {
              ...get().game!,
              play_pile: displayPile,
              running_total: displayTotal,
              player: { ...game.player, score: playerScore },
              opponent: { ...game.opponent, hand_count: oppCount, score: oppScore },
              last_action: action,
              action_log: log.slice(0, i + 1),
            },
          });
        }

        // Update tracking for next iteration
        if (action.action === 'play' && action.card) {
          playPile = displayPile;
          runTotal = displayTotal;
          if (runTotal >= 31) {
            playPile = [];
            runTotal = 0;
          }
        }
      }
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
      playGameOverSound(updated);
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },
}));
