"""Tests for the multiplayer game engine."""

import pytest

from backend.game.deck import create_card
from backend.game.models import GamePhase
from backend.game.multiplayer_engine import MultiplayerGameEngine


def card(rank: str, suit: str = "Hearts"):
    return create_card(suit, rank)


class TestMultiplayerInit:
    def test_initial_state(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        assert eng.phase == GamePhase.DISCARD
        assert eng.round_number == 1
        assert len(eng.player1.hand) == 6
        assert len(eng.player2.hand) == 6
        assert eng.winner is None

    def test_dealer_assignment(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        assert not eng.player1.is_dealer
        assert eng.player2.is_dealer
        assert eng.non_dealer is eng.player1
        assert eng.dealer is eng.player2


class TestMultiplayerDiscard:
    def test_player1_discard(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        state = eng.discard("player1", [0, 1])
        assert eng.player1_discarded
        assert not eng.player2_discarded
        assert len(eng.player1.hand) == 4
        assert len(eng.crib) == 2
        assert eng.phase == GamePhase.DISCARD  # still waiting for player2

    def test_both_discard_transitions_to_play(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        state = eng.discard("player2", [0, 1])
        assert eng.phase == GamePhase.PLAY
        assert len(eng.player1.hand) == 4
        assert len(eng.player2.hand) == 4
        assert len(eng.crib) == 4
        assert eng.starter is not None

    def test_discard_wrong_phase_raises(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        eng.discard("player2", [0, 1])
        # Now in play phase
        with pytest.raises(ValueError, match="Cannot discard"):
            eng.discard("player1", [0, 1])

    def test_double_discard_raises(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        with pytest.raises(ValueError, match="Already discarded"):
            eng.discard("player1", [0, 1])

    def test_discard_wrong_count_raises(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        with pytest.raises(ValueError, match="exactly 2"):
            eng.discard("player1", [0])

    def test_your_turn_discard(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        state1 = eng.get_state("player1")
        assert state1.your_turn is True

        eng.discard("player1", [0, 1])
        state1 = eng.get_state("player1")
        assert state1.your_turn is False  # already discarded

        state2 = eng.get_state("player2")
        assert state2.your_turn is True  # hasn't discarded yet


class TestMultiplayerPlay:
    def _setup_play(self):
        """Get an engine into play phase."""
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        eng.discard("player2", [0, 1])
        assert eng.phase == GamePhase.PLAY
        return eng

    def test_non_dealer_goes_first(self):
        eng = self._setup_play()
        # player1 is non-dealer, player2 is dealer
        assert eng.current_turn == "player1"

    def test_play_card(self):
        eng = self._setup_play()
        hand_before = len(eng.player1_play_hand)
        state = eng.play_card("player1", 0)
        assert len(eng.player1_play_hand) == hand_before - 1
        assert len(eng.play_pile) >= 1

    def test_play_wrong_turn_raises(self):
        eng = self._setup_play()
        with pytest.raises(ValueError, match="Not your turn"):
            eng.play_card("player2", 0)

    def test_play_wrong_phase_raises(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        with pytest.raises(ValueError, match="Cannot play"):
            eng.play_card("player1", 0)

    def test_play_exceeds_31_raises(self):
        eng = self._setup_play()
        eng.running_total = 25
        # Force all cards to be high value
        eng.player1_play_hand = [card("K"), card("Q"), card("J"), card("9")]
        with pytest.raises(ValueError, match="exceed 31"):
            eng.play_card("player1", 0)  # K (10) + 25 = 35

    def test_your_turn_play(self):
        eng = self._setup_play()
        state1 = eng.get_state("player1")
        state2 = eng.get_state("player2")
        assert state1.your_turn is True  # non-dealer's turn
        assert state2.your_turn is False


class TestMultiplayerGo:
    def _setup_play(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        eng.discard("player2", [0, 1])
        return eng

    def test_go_with_playable_cards_raises(self):
        eng = self._setup_play()
        eng.running_total = 0  # Everything is playable
        with pytest.raises(ValueError, match="playable cards"):
            eng.say_go("player1")

    def test_go_switches_turn(self):
        eng = self._setup_play()
        eng.running_total = 28
        eng.player1_play_hand = [card("K")]  # Can't play (10+28=38)
        eng.player2_play_hand = [card("2")]  # Can play (2+28=30)
        eng.say_go("player1")
        assert eng.current_turn == "player2"

    def test_go_logs_action(self):
        eng = self._setup_play()
        eng.running_total = 28
        eng.player1_play_hand = [card("K")]
        eng.player2_play_hand = [card("2")]
        eng.say_go("player1")
        assert eng.last_action is not None
        assert eng.last_action.action == "go"
        assert "Alice" in eng.last_action.message

    def test_both_go_resets_pile(self):
        eng = self._setup_play()
        eng.running_total = 30
        eng.player1_play_hand = [card("K")]  # Can't play
        eng.player2_play_hand = [card("Q")]  # Can't play either
        eng.play_pile = [card("10"), card("10", "Diamonds"), card("10", "Clubs")]

        eng.say_go("player1")
        # After both can't play, pile should reset
        assert eng.running_total == 0


class TestMultiplayerCounting:
    def _play_through(self, eng):
        """Play through all cards until counting begins."""
        max_turns = 50
        for _ in range(max_turns):
            if eng.phase != GamePhase.PLAY:
                return
            current = eng.current_turn
            hand = eng._play_hand(current)
            if not hand:
                break

            # Find playable card
            played = False
            for i, c in enumerate(hand):
                if c.value + eng.running_total <= 31:
                    eng.play_card(current, i)
                    played = True
                    break

            if not played:
                eng.say_go(current)

    def test_counting_sequence(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        eng.discard("player2", [0, 1])
        self._play_through(eng)

        if eng.phase == GamePhase.GAME_OVER:
            return  # Rare but possible with His Heels + pegging

        assert eng.phase == GamePhase.COUNT_NON_DEALER
        eng.acknowledge("player1")
        assert eng.phase == GamePhase.COUNT_DEALER
        eng.acknowledge("player1")
        assert eng.phase == GamePhase.COUNT_CRIB
        eng.acknowledge("player1")
        # Should rotate to next round
        assert eng.phase == GamePhase.DISCARD
        assert eng.round_number == 2

    def test_dealer_swaps_after_round(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        assert eng.player1.is_dealer is False
        assert eng.player2.is_dealer is True

        eng.discard("player1", [0, 1])
        eng.discard("player2", [0, 1])
        self._play_through(eng)

        if eng.phase == GamePhase.GAME_OVER:
            return

        for _ in range(3):
            eng.acknowledge("player1")

        assert eng.player1.is_dealer is True
        assert eng.player2.is_dealer is False

    def test_score_breakdown_populated(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        eng.discard("player1", [0, 1])
        eng.discard("player2", [0, 1])
        self._play_through(eng)

        if eng.phase == GamePhase.GAME_OVER:
            return

        eng.acknowledge("player1")
        assert eng.score_breakdown is not None
        assert eng.score_breakdown.starter == eng.starter


class TestMultiplayerHisHeels:
    def test_his_heels_scores_for_dealer(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        # Force both to discard so we reach the starter cut
        eng.discard("player1", [0, 1])

        # Rig the deck so next card dealt (starter) is a Jack
        eng.deck = [card("J", "Spades")] + eng.deck[1:]
        dealer_score_before = eng.dealer.score

        eng.discard("player2", [0, 1])

        # Dealer (player2) should get 2 points for His Heels
        assert eng.dealer.score == dealer_score_before + 2


class TestMultiplayerGetState:
    def test_opponent_cards_hidden(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        state = eng.get_state("player1")
        # Player can see their own hand
        assert len(state.player.hand) == 6
        # But only a count for opponent
        assert state.opponent.hand_count == 6
        assert state.opponent.name == "Bob"

    def test_state_perspectives_differ(self):
        eng = MultiplayerGameEngine("Alice", "Bob")
        s1 = eng.get_state("player1")
        s2 = eng.get_state("player2")
        assert s1.player.name == "Alice"
        assert s1.opponent.name == "Bob"
        assert s2.player.name == "Bob"
        assert s2.opponent.name == "Alice"
