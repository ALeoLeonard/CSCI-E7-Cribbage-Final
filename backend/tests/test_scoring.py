"""Tests for cribbage scoring — hand scoring and play-phase scoring."""

import pytest

from backend.game.deck import create_card
from backend.game.scoring import calculate_play_score, calculate_score


# --- Helper ---
def card(rank: str, suit: str = "Hearts"):
    return create_card(suit, rank)


# =====================
# Hand scoring tests
# =====================

class TestFifteens:
    def test_simple_fifteen(self):
        hand = [card("5"), card("10"), card("2"), card("3")]
        starter = card("A", "Clubs")
        score, events = calculate_score(hand, starter)
        # 5+10=15 → 2 pts, 2+3+10=15 → 2 pts = 4 pts (plus any runs, etc.)
        fifteens_pts = sum(e.points for e in events if "fifteen" in e.reason.lower())
        assert fifteens_pts >= 4

    def test_no_fifteens(self):
        hand = [card("A"), card("A", "Diamonds"), card("2"), card("3")]
        starter = card("A", "Clubs")
        score, events = calculate_score(hand, starter)
        fifteens_pts = sum(e.points for e in events if "fifteen" in e.reason.lower())
        assert fifteens_pts == 0


class TestPairs:
    def test_pair(self):
        hand = [card("8"), card("8", "Diamonds"), card("A"), card("2")]
        starter = card("K", "Clubs")
        score, events = calculate_score(hand, starter)
        pair_pts = sum(e.points for e in events if "pair" in e.reason.lower() or "two" in e.reason.lower())
        assert pair_pts >= 2

    def test_three_of_a_kind(self):
        hand = [card("7"), card("7", "Diamonds"), card("7", "Clubs"), card("A")]
        starter = card("K", "Spades")
        score, events = calculate_score(hand, starter)
        three_pts = sum(e.points for e in events if "three" in e.reason.lower())
        assert three_pts >= 6

    def test_four_of_a_kind(self):
        hand = [card("9"), card("9", "Diamonds"), card("9", "Clubs"), card("9", "Spades")]
        starter = card("A")
        score, events = calculate_score(hand, starter)
        four_pts = sum(e.points for e in events if "four" in e.reason.lower())
        assert four_pts >= 12


class TestRuns:
    def test_run_of_three(self):
        hand = [card("3"), card("4"), card("5"), card("K")]
        starter = card("A", "Clubs")
        score, events = calculate_score(hand, starter)
        run_pts = sum(e.points for e in events if "run" in e.reason.lower())
        assert run_pts >= 3

    def test_run_of_five(self):
        hand = [card("A"), card("2"), card("3"), card("4")]
        starter = card("5", "Clubs")
        score, events = calculate_score(hand, starter)
        run_pts = sum(e.points for e in events if "run" in e.reason.lower())
        assert run_pts == 5

    def test_double_run(self):
        hand = [card("3"), card("3", "Diamonds"), card("4"), card("5")]
        starter = card("K", "Clubs")
        score, events = calculate_score(hand, starter)
        run_pts = sum(e.points for e in events if "run" in e.reason.lower())
        assert run_pts == 6  # 2x run of 3


class TestFlush:
    def test_four_card_flush(self):
        hand = [card("2", "Hearts"), card("4", "Hearts"), card("8", "Hearts"), card("K", "Hearts")]
        starter = card("A", "Clubs")
        score, events = calculate_score(hand, starter)
        flush_pts = sum(e.points for e in events if "flush" in e.reason.lower())
        assert flush_pts == 4

    def test_five_card_flush(self):
        hand = [card("2", "Hearts"), card("4", "Hearts"), card("8", "Hearts"), card("K", "Hearts")]
        starter = card("A", "Hearts")
        score, events = calculate_score(hand, starter)
        flush_pts = sum(e.points for e in events if "flush" in e.reason.lower())
        assert flush_pts == 5

    def test_no_flush(self):
        hand = [card("2", "Hearts"), card("4", "Diamonds"), card("8", "Hearts"), card("K", "Hearts")]
        starter = card("A", "Hearts")
        score, events = calculate_score(hand, starter)
        flush_pts = sum(e.points for e in events if "flush" in e.reason.lower())
        assert flush_pts == 0


class TestNobs:
    def test_nobs(self):
        hand = [card("J", "Hearts"), card("2"), card("3"), card("4")]
        starter = card("K", "Hearts")
        score, events = calculate_score(hand, starter)
        nobs_pts = sum(e.points for e in events if "nobs" in e.reason.lower())
        assert nobs_pts == 1

    def test_no_nobs_different_suit(self):
        hand = [card("J", "Clubs"), card("2"), card("3"), card("4")]
        starter = card("K", "Hearts")
        score, events = calculate_score(hand, starter)
        nobs_pts = sum(e.points for e in events if "nobs" in e.reason.lower())
        assert nobs_pts == 0


class TestPerfectHand:
    def test_29_hand(self):
        """The perfect cribbage hand: three 5s + J of same suit as starter 5."""
        hand = [
            card("5", "Hearts"),
            card("5", "Diamonds"),
            card("5", "Clubs"),
            card("J", "Spades"),
        ]
        starter = card("5", "Spades")
        score, events = calculate_score(hand, starter)
        assert score == 29


class TestZeroHand:
    def test_zero_hand(self):
        """A hand that scores 0 (rare but possible)."""
        # All even values → no subset sums to 15 (odd). Different suits, non-consecutive, no J.
        hand = [card("2"), card("4", "Diamonds"), card("6", "Clubs"), card("8", "Spades")]
        starter = card("10")
        score, events = calculate_score(hand, starter)
        assert score == 0


# ============================
# Play-phase scoring tests
# ============================

class TestPlayScoring:
    def test_fifteen_during_play(self):
        pile = [card("7"), card("8")]
        events = calculate_play_score(pile, 15)
        assert any(e.points == 2 and "fifteen" in e.reason.lower() for e in events)

    def test_thirty_one_during_play(self):
        pile = [card("10"), card("10", "Diamonds"), card("J")]
        events = calculate_play_score(pile, 31)
        # 31 for 2, also a pair is NOT here because J≠10 rank
        assert any(e.points == 2 and "thirty-one" in e.reason.lower() for e in events)

    def test_pair_during_play(self):
        pile = [card("6"), card("6", "Diamonds")]
        events = calculate_play_score(pile, 12)
        assert any(e.points == 2 and "pair" in e.reason.lower() for e in events)

    def test_three_of_kind_during_play(self):
        pile = [card("4"), card("4", "Diamonds"), card("4", "Clubs")]
        events = calculate_play_score(pile, 12)
        assert any(e.points == 6 and "three" in e.reason.lower() for e in events)

    def test_run_during_play(self):
        pile = [card("3"), card("4"), card("5")]
        events = calculate_play_score(pile, 12)
        assert any(e.points == 3 and "run" in e.reason.lower() for e in events)

    def test_run_not_consecutive_order(self):
        """Run detection should work even if cards were played out of order."""
        pile = [card("5"), card("3"), card("4")]
        events = calculate_play_score(pile, 12)
        assert any(e.points == 3 and "run" in e.reason.lower() for e in events)

    def test_no_scoring(self):
        pile = [card("A"), card("3")]
        events = calculate_play_score(pile, 4)
        assert len(events) == 0
