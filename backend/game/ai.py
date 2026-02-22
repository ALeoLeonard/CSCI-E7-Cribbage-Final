from __future__ import annotations

import random
from itertools import combinations
from typing import Optional

from .models import AIDifficulty, Card
from .scoring import calculate_play_score, calculate_score


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

    _SAMPLE_SIZE = 8

    def choose_discards(self, hand: list[Card], is_dealer: bool) -> list[int]:
        from .deck import create_deck

        all_cards = create_deck()
        hand_set = set(hand)
        remaining_deck = [c for c in all_cards if c not in hand_set]
        sample = random.sample(remaining_deck, min(self._SAMPLE_SIZE, len(remaining_deck)))

        best_avg = -1.0
        best_indices: list[int] = [0, 1]

        for combo in combinations(range(len(hand)), 2):
            kept = [hand[i] for i in range(len(hand)) if i not in combo]
            total = sum(calculate_score(kept, s)[0] for s in sample)
            avg = total / len(sample)
            if avg > best_avg:
                best_avg = avg
                best_indices = list(combo)

        return sorted(best_indices)

    def _pick_play(self, hand: list[Card], playable: list[int], play_pile: list[Card], running_total: int) -> int:
        # Prefer hitting 31 or 15
        for i in playable:
            new_total = running_total + hand[i].value
            if new_total == 31:
                return i
        for i in playable:
            new_total = running_total + hand[i].value
            if new_total == 15:
                return i
        # Try to pair the last card played
        if play_pile:
            last_rank = play_pile[-1].rank
            for i in playable:
                if hand[i].rank == last_rank:
                    return i
        # Avoid leaving total at 5 or 21 (easy 15/31 for opponent)
        safe = [i for i in playable if running_total + hand[i].value not in (5, 21)]
        if safe:
            return random.choice(safe)
        return random.choice(playable)


class HardAI(BaseAI):
    """Full evaluation over expected starters; strategic pegging."""

    @staticmethod
    def _estimate_crib_value(discarded: list[Card]) -> float:
        """Rough estimate of how valuable two discards are in a crib."""
        value = 0.0
        d0, d1 = discarded[0], discarded[1]

        # 5s are extremely valuable in crib (combine with 10-cards for 15s)
        for c in discarded:
            if c.value == 5:
                value += 2.5

        # Cards that sum to 15 are worth ~2 pts
        if d0.value + d1.value == 15:
            value += 2.0

        # Pairs are worth 2 pts
        if d0.rank == d1.rank:
            value += 2.0

        # Adjacent ranks have run potential (~1 pt)
        from .constants import RANK_ORDER
        diff = abs(RANK_ORDER[d0.rank] - RANK_ORDER[d1.rank])
        if diff == 1:
            value += 1.0
        elif diff == 2:
            value += 0.5

        # Same suit has flush potential (~0.5 pt)
        if d0.suit == d1.suit:
            value += 0.5

        return value

    def choose_discards(self, hand: list[Card], is_dealer: bool) -> list[int]:
        from .deck import create_deck

        all_cards = create_deck()
        hand_set = set(hand)

        best_avg = -1.0
        best_indices: list[int] = [0, 1]

        for combo in combinations(range(len(hand)), 2):
            remaining = [hand[i] for i in range(len(hand)) if i not in combo]
            discarded = [hand[i] for i in combo]

            total_score = 0
            count = 0
            for card in all_cards:
                if card not in hand_set:
                    score, _ = calculate_score(remaining, card)
                    total_score += score
                    count += 1

            avg = total_score / count if count else 0

            # Adjust for crib value: dealer's discards help, opponent's hurt
            crib_est = self._estimate_crib_value(discarded)
            if is_dealer:
                avg += crib_est
            else:
                avg -= crib_est

            if avg > best_avg:
                best_avg = avg
                best_indices = list(combo)

        return sorted(best_indices)

    def _pick_play(self, hand: list[Card], playable: list[int], play_pile: list[Card], running_total: int) -> int:
        # Simulate each candidate play and score it
        scored: list[tuple[int, int, float]] = []  # (index, offensive_pts, defensive_penalty)
        for i in playable:
            card = hand[i]
            new_total = running_total + card.value
            sim_pile = play_pile + [card]
            events = calculate_play_score(sim_pile, new_total)
            pts = sum(e.points for e in events)

            # Defensive penalty: how easy is it for opponent to score off our play?
            penalty = 0.0
            # Leaving total at 5 or 21 lets opponent hit 15 or 31 easily
            if new_total in (5, 21):
                penalty += 2.0
            # Leaving a pair setup (opponent can triple)
            if play_pile and play_pile[-1].rank == card.rank:
                # We're making a pair — good offensively, but opponent could triple
                pass
            elif new_total < 31:
                # Exposing our rank for a pair opportunity
                penalty += 0.3

            scored.append((i, pts, penalty))

        # Pick: highest (pts - penalty), break ties randomly
        scored.sort(key=lambda x: (x[1] - x[2], random.random()), reverse=True)
        return scored[0][0]


def create_ai(difficulty: AIDifficulty) -> BaseAI:
    if difficulty == AIDifficulty.EASY:
        return EasyAI()
    elif difficulty == AIDifficulty.MEDIUM:
        return MediumAI()
    else:
        return HardAI()
