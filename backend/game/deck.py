from __future__ import annotations

import random
from typing import List, Tuple

from .constants import RANKS, SUITS
from .models import Card, Suit


def create_card(suit: str, rank: str) -> Card:
    if rank in ("J", "Q", "K"):
        value = 10
    elif rank == "A":
        value = 1
    else:
        value = int(rank)
    return Card(suit=Suit(suit), rank=rank, value=value)


def create_deck() -> list[Card]:
    return [create_card(suit, rank) for suit in SUITS for rank in RANKS]


def shuffle_deck(deck: list[Card]) -> list[Card]:
    shuffled = deck.copy()
    random.shuffle(shuffled)
    return shuffled


def deal(deck: list[Card], n: int) -> tuple[list[Card], list[Card]]:
    """Deal n cards from top of deck. Returns (dealt, remaining)."""
    return deck[:n], deck[n:]
