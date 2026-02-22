export type Suit = 'Hearts' | 'Diamonds' | 'Clubs' | 'Spades';

export interface Card {
  suit: Suit;
  rank: string;
  value: number;
}

export type GamePhase =
  | 'discard'
  | 'play'
  | 'count_non_dealer'
  | 'count_dealer'
  | 'count_crib'
  | 'game_over';

export type AIDifficulty = 'easy' | 'medium' | 'hard';

export interface ScoreEvent {
  player: string;
  points: number;
  reason: string;
}

export interface LastAction {
  actor: string;
  action: string;
  card?: Card;
  score_events: ScoreEvent[];
  message: string;
}

export interface PlayerView {
  name: string;
  hand: Card[];
  score: number;
  is_dealer: boolean;
}

export interface OpponentView {
  name: string;
  hand_count: number;
  score: number;
  is_dealer: boolean;
}

export interface ScoreBreakdown {
  hand: Card[];
  starter: Card;
  items: ScoreEvent[];
  total: number;
}

export interface GameStatsData {
  hand_scores: number[];
  crib_scores: number[];
  highest_hand_score: number;
  total_points_scored: number;
}

export interface GameState {
  game_id: string;
  phase: GamePhase;
  player: PlayerView;
  opponent: OpponentView;
  starter?: Card;
  crib_count: number;
  play_pile: Card[];
  running_total: number;
  last_action?: LastAction;
  action_log: LastAction[];
  score_breakdown?: ScoreBreakdown;
  winner?: string;
  round_number: number;
  your_turn: boolean;
  game_stats?: GameStatsData;
}

export interface RecordGamePayload {
  player_name: string;
  opponent_name: string;
  player_score: number;
  opponent_score: number;
  won: boolean;
  ai_difficulty?: string;
  game_mode: string;
  hand_scores: number[];
  crib_scores: number[];
  highest_hand_score: number;
  total_points_scored: number;
}

export interface DifficultyStats {
  difficulty: string;
  games: number;
  wins: number;
  losses: number;
  win_rate: number;
}

export interface PlayerStats {
  player_name: string;
  games: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_hand_score: number;
  avg_crib_score: number;
  best_hand: number;
  total_points: number;
  current_streak: number;
  best_win_streak: number;
  per_difficulty: DifficultyStats[];
}
