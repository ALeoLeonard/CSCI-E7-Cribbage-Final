from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Suit(str, Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"


class Card(BaseModel):
    suit: Suit
    rank: str
    value: int  # scoring value: A=1, 2-10 face, J/Q/K=10

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

    @property
    def label(self) -> str:
        from .constants import SUIT_EMOJIS
        return f"{self.rank}{SUIT_EMOJIS[self.suit.value]}"


class GamePhase(str, Enum):
    DISCARD = "discard"
    PLAY = "play"
    COUNT_NON_DEALER = "count_non_dealer"
    COUNT_DEALER = "count_dealer"
    COUNT_CRIB = "count_crib"
    GAME_OVER = "game_over"


class AIDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ScoreEvent(BaseModel):
    player: str
    points: int
    reason: str


class LastAction(BaseModel):
    actor: str
    action: str  # "play", "go", "discard", "score"
    card: Optional[Card] = None
    score_events: list[ScoreEvent] = Field(default_factory=list)
    message: str = ""


class PlayerState(BaseModel):
    """Full server-side player state (never sent directly to client)."""
    name: str
    hand: list[Card] = Field(default_factory=list)
    score: int = 0
    is_dealer: bool = False


class PlayerView(BaseModel):
    """What the client sees about themselves."""
    name: str
    hand: list[Card]
    score: int
    is_dealer: bool


class OpponentView(BaseModel):
    """What the client sees about their opponent — no cards!"""
    name: str
    hand_count: int
    score: int
    is_dealer: bool


class ScoreBreakdown(BaseModel):
    hand: list[Card]
    starter: Card
    items: list[ScoreEvent]
    total: int


class GameStatsData(BaseModel):
    """Per-player scoring stats collected during a game."""
    hand_scores: list[int] = Field(default_factory=list)
    crib_scores: list[int] = Field(default_factory=list)
    highest_hand_score: int = 0
    total_points_scored: int = 0


class GameStateResponse(BaseModel):
    """The full response sent to the frontend."""
    game_id: str
    phase: GamePhase
    player: PlayerView
    opponent: OpponentView
    starter: Optional[Card] = None
    crib_count: int = 0
    play_pile: list[Card] = Field(default_factory=list)
    running_total: int = 0
    last_action: Optional[LastAction] = None
    action_log: list[LastAction] = Field(default_factory=list)
    score_breakdown: Optional[ScoreBreakdown] = None
    winner: Optional[str] = None
    round_number: int = 1
    your_turn: bool = True
    game_stats: Optional[GameStatsData] = None


class NewGameRequest(BaseModel):
    player_name: str = "Player"
    ai_difficulty: AIDifficulty = AIDifficulty.EASY


class DiscardRequest(BaseModel):
    card_indices: list[int]  # exactly 2 indices


class PlayCardRequest(BaseModel):
    card_index: int


class RecordGameRequest(BaseModel):
    player_name: str
    opponent_name: str
    player_score: int
    opponent_score: int
    won: bool
    ai_difficulty: Optional[str] = None
    game_mode: str = "single"  # "single" or "multiplayer"
    hand_scores: list[int] = Field(default_factory=list)
    crib_scores: list[int] = Field(default_factory=list)
    highest_hand_score: int = 0
    total_points_scored: int = 0


class DifficultyStats(BaseModel):
    difficulty: str
    games: int
    wins: int
    losses: int
    win_rate: float


class PlayerStatsResponse(BaseModel):
    player_name: str
    games: int
    wins: int
    losses: int
    win_rate: float
    avg_hand_score: float
    avg_crib_score: float
    best_hand: int
    total_points: int
    current_streak: int  # positive = win streak, negative = loss streak
    best_win_streak: int
    per_difficulty: list[DifficultyStats] = Field(default_factory=list)
