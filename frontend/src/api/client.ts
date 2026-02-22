import type { AIDifficulty, GameState, PlayerStats, RecordGamePayload } from './types';

const BASE = '/api/v1/game';
const STATS_BASE = '/api/v1/stats';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return resp.json();
}

export const api = {
  newGame(playerName: string, difficulty: AIDifficulty): Promise<GameState> {
    return request(`${BASE}/new`, {
      method: 'POST',
      body: JSON.stringify({ player_name: playerName, ai_difficulty: difficulty }),
    });
  },

  getGame(gameId: string): Promise<GameState> {
    return request(`${BASE}/${gameId}`);
  },

  discard(gameId: string, cardIndices: number[]): Promise<GameState> {
    return request(`${BASE}/${gameId}/discard`, {
      method: 'POST',
      body: JSON.stringify({ card_indices: cardIndices }),
    });
  },

  playCard(gameId: string, cardIndex: number): Promise<GameState> {
    return request(`${BASE}/${gameId}/play`, {
      method: 'POST',
      body: JSON.stringify({ card_index: cardIndex }),
    });
  },

  sayGo(gameId: string): Promise<GameState> {
    return request(`${BASE}/${gameId}/go`, { method: 'POST' });
  },

  acknowledge(gameId: string): Promise<GameState> {
    return request(`${BASE}/${gameId}/acknowledge`, { method: 'POST' });
  },

  recordGame(payload: RecordGamePayload): Promise<{ status: string }> {
    return request(`${STATS_BASE}/record`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getStats(playerName: string): Promise<PlayerStats> {
    return request(`${STATS_BASE}/${encodeURIComponent(playerName)}`);
  },
};
