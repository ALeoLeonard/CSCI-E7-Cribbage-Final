import { create } from 'zustand';
import { api } from '../api/client';
import type { PlayerStats, RecordGamePayload } from '../api/types';

const STORAGE_KEY = 'cribbage_stats';

interface StatsStore {
  stats: PlayerStats | null;
  loading: boolean;

  loadStats: (playerName: string) => Promise<void>;
  recordGame: (payload: RecordGamePayload) => void;
}

function emptyStats(playerName: string): PlayerStats {
  return {
    player_name: playerName,
    games: 0, wins: 0, losses: 0, win_rate: 0,
    avg_hand_score: 0, avg_crib_score: 0, best_hand: 0, total_points: 0,
    current_streak: 0, best_win_streak: 0, per_difficulty: [],
  };
}

function loadLocalStats(playerName: string): PlayerStats | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as PlayerStats;
    if (data.player_name === playerName) return data;
    return null;
  } catch {
    return null;
  }
}

function saveLocalStats(stats: PlayerStats): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
  } catch {
    // localStorage full or unavailable
  }
}

function mergeLocalStats(prev: PlayerStats, payload: RecordGamePayload): PlayerStats {
  const games = prev.games + 1;
  const wins = prev.wins + (payload.won ? 1 : 0);
  const losses = games - wins;

  // Incremental average recalculation
  const allHandCount = prev.games > 0
    ? Math.round(prev.avg_hand_score > 0 ? prev.games * 2 : 0) // approximation
    : 0;
  const newHandCount = allHandCount + payload.hand_scores.length;
  const avgHand = newHandCount > 0
    ? Math.round(((prev.avg_hand_score * allHandCount) + payload.hand_scores.reduce((a, b) => a + b, 0)) / newHandCount * 10) / 10
    : 0;

  const allCribCount = prev.games > 0
    ? Math.round(prev.avg_crib_score > 0 ? prev.games : 0)
    : 0;
  const newCribCount = allCribCount + payload.crib_scores.length;
  const avgCrib = newCribCount > 0
    ? Math.round(((prev.avg_crib_score * allCribCount) + payload.crib_scores.reduce((a, b) => a + b, 0)) / newCribCount * 10) / 10
    : 0;

  // Streak calculation
  let currentStreak = prev.current_streak;
  if (payload.won) {
    currentStreak = currentStreak > 0 ? currentStreak + 1 : 1;
  } else {
    currentStreak = currentStreak < 0 ? currentStreak - 1 : -1;
  }
  const bestWinStreak = Math.max(prev.best_win_streak, currentStreak > 0 ? currentStreak : 0);

  // Per-difficulty
  const diffMap = new Map(prev.per_difficulty.map(d => [d.difficulty, { ...d }]));
  const diffKey = payload.ai_difficulty || 'multiplayer';
  const existing = diffMap.get(diffKey) || { difficulty: diffKey, games: 0, wins: 0, losses: 0, win_rate: 0 };
  existing.games++;
  if (payload.won) existing.wins++;
  existing.losses = existing.games - existing.wins;
  existing.win_rate = Math.round(existing.wins / existing.games * 1000) / 10;
  diffMap.set(diffKey, existing);

  return {
    player_name: prev.player_name,
    games,
    wins,
    losses,
    win_rate: Math.round(wins / games * 1000) / 10,
    avg_hand_score: avgHand,
    avg_crib_score: avgCrib,
    best_hand: Math.max(prev.best_hand, payload.highest_hand_score),
    total_points: prev.total_points + payload.total_points_scored,
    current_streak: currentStreak,
    best_win_streak: bestWinStreak,
    per_difficulty: Array.from(diffMap.values()),
  };
}

export const useStatsStore = create<StatsStore>((set) => ({
  stats: null,
  loading: false,

  loadStats: async (playerName: string) => {
    // Show local stats immediately
    const local = loadLocalStats(playerName);
    set({ stats: local || emptyStats(playerName), loading: true });

    try {
      const remote = await api.getStats(playerName);
      set({ stats: remote, loading: false });
      saveLocalStats(remote);
    } catch {
      // Backend unavailable — keep local stats
      set({ loading: false });
    }
  },

  recordGame: (payload: RecordGamePayload) => {
    // Update localStorage immediately
    const local = loadLocalStats(payload.player_name) || emptyStats(payload.player_name);
    const updated = mergeLocalStats(local, payload);
    saveLocalStats(updated);
    set({ stats: updated });

    // Fire-and-forget to backend
    api.recordGame(payload).catch(() => {
      // Backend unavailable — stats are still in localStorage
    });
  },
}));
