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
}
