"""Stateless play-phase (pegging) logic.

Each call to `process_play` handles one card being played and returns
the resulting state. No loops — the frontend drives turn-by-turn via API calls.
"""

from __future__ import annotations

from .models import Card, ScoreEvent
from .scoring import calculate_play_score


def can_play(hand: list[Card], running_total: int) -> bool:
    """Check if any card in hand can be played without exceeding 31."""
    return any(c.value + running_total <= 31 for c in hand)


def process_play(
    card: Card,
    play_pile: list[Card],
    running_total: int,
) -> tuple[list[Card], int, list[ScoreEvent]]:
    """
    Process a single card being played.
    Returns (new_pile, new_running_total, score_events).
    """
    new_pile = play_pile + [card]
    new_total = running_total + card.value
    events = calculate_play_score(new_pile, new_total)
    return new_pile, new_total, events


def process_go(
    running_total: int,
    player_hand: list[Card],
    opponent_hand: list[Card],
) -> tuple[int, bool]:
    """
    Handle a 'Go' situation.
    Returns (points_for_opponent, should_reset_total).
    If neither player can play, award 1 point for last card and reset.
    """
    opponent_can = can_play(opponent_hand, running_total)
    if opponent_can:
        # Opponent continues, no reset yet
        return 1, False
    else:
        # Neither can play — 1 point for last card, reset
        return 1, True
