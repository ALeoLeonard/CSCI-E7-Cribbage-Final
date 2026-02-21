from __future__ import annotations

import random
from itertools import combinations
from typing import Optional

from .models import AIDifficulty, Card
from .scoring import calculate_score


class BaseAI:
    def choose_discards(self, hand: list[Card], is_dealer: bool) -> list[int]:
        raise NotImplementedError

    def choose_play(self, hand: list[Card], play_pile: list[Card], running_total: int) -> Optional[int]:
        """Return index of card to play, or None if no valid card (Go)."""
        playable = [
            i for i, c in enumerate(hand) if c.value + running_total <= 31
        ]
        if not playable:
            return None
        return self._pick_play(hand, playable, play_pile, running_total)

    def _pick_play(self, hand: list[Card], playable: list[int], play_pile: list[Card], running_total: int) -> int:
        raise NotImplementedError


class EasyAI(BaseAI):
    """Random discards, random play."""

    def choose_discards(self, hand: list[Card], is_dealer: bool) -> list[int]:
        return sorted(random.sample(range(len(hand)), 2))

    def _pick_play(self, hand: list[Card], playable: list[int], play_pile: list[Card], running_total: int) -> int:
        return random.choice(playable)


class MediumAI(BaseAI):
    """Evaluates discard combos to maximize hand score. Smarter pegging."""

    def choose_discards(self, hand: list[Card], is_dealer: bool) -> list[int]:
        best_score = -1
        best_indices: list[int] = [0, 1]

        for combo in combinations(range(len(hand)), 2):
            remaining = [hand[i] for i in range(len(hand)) if i not in combo]
            # Use the first discard as a pseudo-starter for quick eval
            dummy_starter = hand[combo[0]]
            score, _ = calculate_score(remaining, dummy_starter)
            if score > best_score:
                best_score = score
                best_indices = list(combo)

        return sorted(best_indices)

    def _pick_play(self, hand: list[Card], playable: list[int], play_pile: list[Card], running_total: int) -> int:
        # Prefer hitting 15 or 31
        for i in playable:
            new_total = running_total + hand[i].value
            if new_total == 15 or new_total == 31:
                return i
        # Avoid leaving total at 5 or 21 (easy 15/31 for opponent)
        safe = [i for i in playable if running_total + hand[i].value not in (5, 21)]
        if safe:
            return random.choice(safe)
        return random.choice(playable)


class HardAI(BaseAI):
    """Full evaluation over expected starters; strategic pegging."""

    def choose_discards(self, hand: list[Card], is_dealer: bool) -> list[int]:
        from .deck import create_deck

        all_cards = create_deck()
        hand_set = set(hand)

        best_avg = -1.0
        best_indices: list[int] = [0, 1]

        for combo in combinations(range(len(hand)), 2):
            remaining = [hand[i] for i in range(len(hand)) if i not in combo]
            discarded = {hand[i] for i in combo}
            remaining_set = set(remaining)

            total_score = 0
            count = 0
            for card in all_cards:
                if card not in hand_set:
                    score, _ = calculate_score(remaining, card)
                    total_score += score
                    count += 1

            avg = total_score / count if count else 0

            # If we're the dealer, our discards go to OUR crib — bonus
            # If not dealer, discards go to opponent's crib — penalty
            if is_dealer:
                avg += 2.5  # rough crib bonus
            else:
                avg -= 1.5  # rough crib penalty

            if avg > best_avg:
                best_avg = avg
                best_indices = list(combo)

        return sorted(best_indices)

    def _pick_play(self, hand: list[Card], playable: list[int], play_pile: list[Card], running_total: int) -> int:
        # Priority: hit 31, hit 15, pair the last card, avoid 5/21
        for i in playable:
            if running_total + hand[i].value == 31:
                return i
        for i in playable:
            if running_total + hand[i].value == 15:
                return i
        if play_pile:
            last_rank = play_pile[-1].rank
            for i in playable:
                if hand[i].rank == last_rank:
                    return i
        safe = [i for i in playable if running_total + hand[i].value not in (5, 21)]
        if safe:
            return random.choice(safe)
        return random.choice(playable)


def create_ai(difficulty: AIDifficulty) -> BaseAI:
    if difficulty == AIDifficulty.EASY:
        return EasyAI()
    elif difficulty == AIDifficulty.MEDIUM:
        return MediumAI()
    else:
        return HardAI()
