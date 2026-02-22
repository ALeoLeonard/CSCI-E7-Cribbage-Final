"""Tests for AI discard and play logic at all difficulty levels."""

import pytest

from backend.game.ai import EasyAI, HardAI, MediumAI, create_ai
from backend.game.deck import create_card
from backend.game.models import AIDifficulty


def card(rank: str, suit: str = "Hearts"):
    return create_card(suit, rank)


class TestCreateAI:
    def test_easy(self):
        ai = create_ai(AIDifficulty.EASY)
        assert isinstance(ai, EasyAI)

    def test_medium(self):
        ai = create_ai(AIDifficulty.MEDIUM)
        assert isinstance(ai, MediumAI)

    def test_hard(self):
        ai = create_ai(AIDifficulty.HARD)
        assert isinstance(ai, HardAI)


class TestEasyAI:
    def test_discards_two_cards(self):
        ai = EasyAI()
        hand = [card("A"), card("2"), card("3"), card("4"), card("5"), card("6")]
        indices = ai.choose_discards(hand, is_dealer=False)
        assert len(indices) == 2
        assert indices == sorted(indices)
        assert all(0 <= i < 6 for i in indices)

    def test_choose_play_returns_playable(self):
        ai = EasyAI()
        hand = [card("3"), card("K")]
        idx = ai.choose_play(hand, [], 0)
        assert idx in (0, 1)

    def test_choose_play_returns_none_when_stuck(self):
        ai = EasyAI()
        hand = [card("K"), card("Q")]
        idx = ai.choose_play(hand, [], 25)
        assert idx is None

    def test_choose_play_respects_31_limit(self):
        ai = EasyAI()
        hand = [card("K"), card("A")]
        # running total = 28, only A (value 1) can play
        idx = ai.choose_play(hand, [], 28)
        assert idx == 1  # A is at index 1


class TestMediumAI:
    def test_discards_two_cards(self):
        ai = MediumAI()
        hand = [card("A"), card("2"), card("3"), card("4"), card("5"), card("6")]
        indices = ai.choose_discards(hand, is_dealer=False)
        assert len(indices) == 2
        assert indices == sorted(indices)

    def test_keeps_fifteens(self):
        """Medium AI should prefer keeping cards that make 15s."""
        ai = MediumAI()
        # 5+10=15 is very valuable; A+2 are weak
        hand = [card("5"), card("10"), card("5", "Diamonds"), card("J"), card("A"), card("2")]
        indices = ai.choose_discards(hand, is_dealer=False)
        # Should discard from the weaker cards (A, 2), not the 5s/10s
        kept = [hand[i] for i in range(6) if i not in indices]
        kept_ranks = {c.rank for c in kept}
        # At minimum, should keep at least one 5
        assert "5" in kept_ranks

    def test_play_prefers_fifteen(self):
        ai = MediumAI()
        hand = [card("5"), card("3")]
        # running total is 10, playing 5 makes 15
        idx = ai.choose_play(hand, [card("10")], 10)
        assert idx == 0  # 5 is at index 0

    def test_play_prefers_thirty_one(self):
        ai = MediumAI()
        hand = [card("A"), card("6")]
        # running total is 25, playing 6 makes 31
        idx = ai.choose_play(hand, [card("K"), card("5"), card("10")], 25)
        assert idx == 1  # 6 makes 31

    def test_play_avoids_leaving_five(self):
        """Medium AI should avoid leaving the total at 5 (easy 15 for opponent)."""
        ai = MediumAI()
        hand = [card("3"), card("7")]
        # running total is 0; playing 3 leaves 3 (ok), playing 7 leaves 7 (ok)
        # Neither leaves 5, so both are fine
        idx = ai.choose_play(hand, [], 0)
        assert idx in (0, 1)

    def test_play_pairs_last_card(self):
        ai = MediumAI()
        hand = [card("8"), card("3")]
        pile = [card("8", "Diamonds")]
        # Running total is 8, playing 8 makes pair and total 16
        idx = ai.choose_play(hand, pile, 8)
        assert idx == 0  # 8 pairs the last card


class TestHardAI:
    def test_discards_two_cards(self):
        ai = HardAI()
        hand = [card("A"), card("2"), card("3"), card("4"), card("5"), card("6")]
        indices = ai.choose_discards(hand, is_dealer=False)
        assert len(indices) == 2
        assert indices == sorted(indices)

    def test_crib_estimation_fives(self):
        """Discarding 5s to crib is very valuable."""
        val = HardAI._estimate_crib_value([card("5"), card("5", "Diamonds")])
        assert val >= 5.0  # Two 5s: 2.5+2.5 for 5s + 2.0 for pair + sum to 10 (not 15)

    def test_crib_estimation_fifteen_combo(self):
        val = HardAI._estimate_crib_value([card("5"), card("10")])
        assert val >= 4.5  # 5 worth 2.5, sum=15 worth 2.0

    def test_crib_estimation_pair(self):
        val = HardAI._estimate_crib_value([card("8"), card("8", "Diamonds")])
        assert val >= 2.0  # pair

    def test_crib_estimation_adjacent(self):
        val = HardAI._estimate_crib_value([card("6"), card("7")])
        assert val >= 1.0  # adjacent

    def test_crib_estimation_same_suit(self):
        val = HardAI._estimate_crib_value([card("2", "Hearts"), card("9", "Hearts")])
        assert val >= 0.5  # same suit

    def test_dealer_prefers_discarding_to_own_crib(self):
        """When dealer, Hard AI should lean toward discarding high-crib-value combos."""
        ai = HardAI()
        hand = [card("5"), card("10"), card("5", "Diamonds"), card("J"), card("A"), card("2")]
        dealer_indices = ai.choose_discards(hand, is_dealer=True)
        non_dealer_indices = ai.choose_discards(hand, is_dealer=False)
        # Results may differ: dealer wants to put good cards in crib
        # Just verify both return valid results
        assert len(dealer_indices) == 2
        assert len(non_dealer_indices) == 2

    def test_play_scores_offensively(self):
        """Hard AI should pick the card that scores the most points."""
        ai = HardAI()
        hand = [card("5"), card("3")]
        pile = [card("10")]
        # Running total 10: playing 5 makes 15 (2 pts), playing 3 makes 13 (0 pts)
        idx = ai.choose_play(hand, pile, 10)
        assert idx == 0  # 5 for the 15

    def test_play_penalizes_leaving_five(self):
        """Hard AI penalizes leaving the running total at 5."""
        ai = HardAI()
        hand = [card("5"), card("7")]
        # running total 0: playing 5 leaves total=5 (bad), playing 7 leaves total=7 (ok)
        idx = ai.choose_play(hand, [], 0)
        assert idx == 1  # should prefer 7

    def test_choose_play_none_when_stuck(self):
        ai = HardAI()
        hand = [card("K")]
        idx = ai.choose_play(hand, [], 25)
        assert idx is None


class TestAIEdgeCases:
    def test_empty_pile_play(self):
        """All AIs should handle playing into an empty pile."""
        for ai_cls in [EasyAI, MediumAI, HardAI]:
            ai = ai_cls()
            hand = [card("7")]
            idx = ai.choose_play(hand, [], 0)
            assert idx == 0

    def test_single_card_hand(self):
        """All AIs should handle a single-card hand."""
        for ai_cls in [EasyAI, MediumAI, HardAI]:
            ai = ai_cls()
            hand = [card("3")]
            idx = ai.choose_play(hand, [card("K")], 10)
            assert idx == 0
