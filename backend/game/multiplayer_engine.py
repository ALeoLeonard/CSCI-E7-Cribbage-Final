"""Multiplayer game engine — two humans, turn validation, per-player views."""

from __future__ import annotations

import uuid
from typing import Optional

from .constants import WINNING_SCORE
from .deck import create_deck, deal, shuffle_deck
from .models import (
    Card,
    GamePhase,
    GameStateResponse,
    LastAction,
    OpponentView,
    PlayerState,
    PlayerView,
    ScoreBreakdown,
    ScoreEvent,
)
from .play_phase import can_play
from .scoring import calculate_play_score, calculate_score


class MultiplayerGameEngine:
    def __init__(self, player1_name: str, player2_name: str):
        self.game_id = str(uuid.uuid4())
        self.phase = GamePhase.DISCARD
        self.round_number = 1

        self.player1 = PlayerState(name=player1_name, is_dealer=False)
        self.player2 = PlayerState(name=player2_name, is_dealer=True)

        self.deck: list[Card] = []
        self.starter: Optional[Card] = None
        self.crib: list[Card] = []

        self.play_pile: list[Card] = []
        self.running_total: int = 0
        self.player1_play_hand: list[Card] = []
        self.player2_play_hand: list[Card] = []
        self.current_turn: str = ""  # "player1" or "player2"
        self.last_go_by: Optional[str] = None

        # Track who has discarded
        self.player1_discarded: bool = False
        self.player2_discarded: bool = False

        self.last_action: Optional[LastAction] = None
        self.score_breakdown: Optional[ScoreBreakdown] = None
        self.winner: Optional[str] = None

        self._deal_round()

    @property
    def dealer(self) -> PlayerState:
        return self.player1 if self.player1.is_dealer else self.player2

    @property
    def non_dealer(self) -> PlayerState:
        return self.player2 if self.player1.is_dealer else self.player1

    def _player_by_id(self, player_id: str) -> PlayerState:
        if player_id == "player1":
            return self.player1
        return self.player2

    def _opponent_by_id(self, player_id: str) -> PlayerState:
        if player_id == "player1":
            return self.player2
        return self.player1

    def _play_hand(self, player_id: str) -> list[Card]:
        return self.player1_play_hand if player_id == "player1" else self.player2_play_hand

    def _deal_round(self) -> None:
        self.deck = shuffle_deck(create_deck())
        p1_cards, self.deck = deal(self.deck, 6)
        p2_cards, self.deck = deal(self.deck, 6)
        self.player1.hand = p1_cards
        self.player2.hand = p2_cards
        self.crib = []
        self.starter = None
        self.play_pile = []
        self.running_total = 0
        self.last_go_by = None
        self.score_breakdown = None
        self.player1_discarded = False
        self.player2_discarded = False
        self.phase = GamePhase.DISCARD

    def _check_winner(self) -> bool:
        if self.player1.score >= WINNING_SCORE:
            self.winner = self.player1.name
            self.phase = GamePhase.GAME_OVER
            return True
        if self.player2.score >= WINNING_SCORE:
            self.winner = self.player2.name
            self.phase = GamePhase.GAME_OVER
            return True
        return False

    def discard(self, player_id: str, card_indices: list[int]) -> GameStateResponse:
        if self.phase != GamePhase.DISCARD:
            raise ValueError("Cannot discard now")
        if len(card_indices) != 2:
            raise ValueError("Must discard exactly 2 cards")

        player = self._player_by_id(player_id)
        already = self.player1_discarded if player_id == "player1" else self.player2_discarded
        if already:
            raise ValueError("Already discarded")

        discarded = [player.hand[i] for i in sorted(card_indices, reverse=True)]
        for i in sorted(card_indices, reverse=True):
            player.hand.pop(i)
        self.crib.extend(discarded)

        if player_id == "player1":
            self.player1_discarded = True
        else:
            self.player2_discarded = True

        # Both discarded? Move to play phase
        if self.player1_discarded and self.player2_discarded:
            starter_cards, self.deck = deal(self.deck, 1)
            self.starter = starter_cards[0]

            if self.starter.rank == "J":
                self.dealer.score += 2
                if self._check_winner():
                    return self.get_state(player_id)

            self.player1_play_hand = self.player1.hand.copy()
            self.player2_play_hand = self.player2.hand.copy()
            self.current_turn = "player1" if not self.player1.is_dealer else "player2"
            self.phase = GamePhase.PLAY

        return self.get_state(player_id)

    def play_card(self, player_id: str, card_index: int) -> GameStateResponse:
        if self.phase != GamePhase.PLAY:
            raise ValueError("Cannot play now")
        if self.current_turn != player_id:
            raise ValueError("Not your turn")

        hand = self._play_hand(player_id)
        if card_index < 0 or card_index >= len(hand):
            raise ValueError("Invalid card index")

        card = hand[card_index]
        if card.value + self.running_total > 31:
            raise ValueError("Card would exceed 31")

        hand.pop(card_index)
        self.play_pile.append(card)
        self.running_total += card.value

        events = calculate_play_score(self.play_pile, self.running_total)
        player = self._player_by_id(player_id)
        total_pts = sum(e.points for e in events)
        if total_pts > 0:
            player.score += total_pts
            for e in events:
                e.player = player.name

        self.last_action = LastAction(
            actor=player.name, action="play", card=card,
            score_events=events, message=f"{player.name} plays {card.label}",
        )

        if self.running_total == 31:
            self.play_pile = []
            self.running_total = 0
            self.last_go_by = None

        if self._check_winner():
            return self.get_state(player_id)

        if not self.player1_play_hand and not self.player2_play_hand:
            self._end_play_phase()
            return self.get_state(player_id)

        # Switch turn
        other_id = "player2" if player_id == "player1" else "player1"
        other_hand = self._play_hand(other_id)
        if other_hand and can_play(other_hand, self.running_total):
            self.current_turn = other_id
        elif hand and can_play(hand, self.running_total):
            pass  # keep same player's turn
        else:
            self._handle_go_both()

        return self.get_state(player_id)

    def say_go(self, player_id: str) -> GameStateResponse:
        if self.phase != GamePhase.PLAY or self.current_turn != player_id:
            raise ValueError("Cannot say Go now")

        hand = self._play_hand(player_id)
        if can_play(hand, self.running_total):
            raise ValueError("You have playable cards")

        player = self._player_by_id(player_id)
        self.last_action = LastAction(
            actor=player.name, action="go", card=None,
            score_events=[], message=f"{player.name} says Go!",
        )

        other_id = "player2" if player_id == "player1" else "player1"
        other_hand = self._play_hand(other_id)

        if self.last_go_by is not None and self.last_go_by != player_id:
            # Both said go
            self._handle_go_both()
        elif other_hand and can_play(other_hand, self.running_total):
            self.last_go_by = player_id
            self.current_turn = other_id
        else:
            self._handle_go_both()

        return self.get_state(player_id)

    def _handle_go_both(self) -> None:
        if self.play_pile and self.last_action:
            target_name = self.last_action.actor
            target = self.player1 if target_name == self.player1.name else self.player2
            target.score += 1
            self._check_winner()
        self.play_pile = []
        self.running_total = 0
        self.last_go_by = None

        if not self.player1_play_hand and not self.player2_play_hand:
            self._end_play_phase()

    def _end_play_phase(self) -> None:
        if self.running_total > 0 and self.last_action:
            target_name = self.last_action.actor
            target = self.player1 if target_name == self.player1.name else self.player2
            target.score += 1
            self._check_winner()
        self.play_pile = []
        self.running_total = 0
        self.phase = GamePhase.COUNT_NON_DEALER

    def acknowledge(self, player_id: str) -> GameStateResponse:
        if self.phase == GamePhase.COUNT_NON_DEALER:
            score, events = calculate_score(self.non_dealer.hand, self.starter)
            for e in events:
                e.player = self.non_dealer.name
            self.non_dealer.score += score
            self.score_breakdown = ScoreBreakdown(
                hand=self.non_dealer.hand, starter=self.starter, items=events, total=score
            )
            if self._check_winner():
                return self.get_state(player_id)
            self.phase = GamePhase.COUNT_DEALER

        elif self.phase == GamePhase.COUNT_DEALER:
            score, events = calculate_score(self.dealer.hand, self.starter)
            for e in events:
                e.player = self.dealer.name
            self.dealer.score += score
            self.score_breakdown = ScoreBreakdown(
                hand=self.dealer.hand, starter=self.starter, items=events, total=score
            )
            if self._check_winner():
                return self.get_state(player_id)
            self.phase = GamePhase.COUNT_CRIB

        elif self.phase == GamePhase.COUNT_CRIB:
            score, events = calculate_score(self.crib, self.starter, is_crib=True)
            for e in events:
                e.player = self.dealer.name
            self.dealer.score += score
            self.score_breakdown = ScoreBreakdown(
                hand=self.crib, starter=self.starter, items=events, total=score
            )
            if self._check_winner():
                return self.get_state(player_id)
            # Swap dealer, new round
            self.player1.is_dealer = not self.player1.is_dealer
            self.player2.is_dealer = not self.player2.is_dealer
            self.round_number += 1
            self._deal_round()

        return self.get_state(player_id)

    def get_state(self, player_id: str) -> GameStateResponse:
        player = self._player_by_id(player_id)
        opp = self._opponent_by_id(player_id)

        if self.phase == GamePhase.PLAY:
            hand = self._play_hand(player_id)
            opp_count = len(self._play_hand("player2" if player_id == "player1" else "player1"))
        else:
            hand = player.hand
            opp_count = len(opp.hand)

        your_turn = True
        if self.phase == GamePhase.PLAY:
            your_turn = self.current_turn == player_id
        elif self.phase == GamePhase.DISCARD:
            already = self.player1_discarded if player_id == "player1" else self.player2_discarded
            your_turn = not already

        return GameStateResponse(
            game_id=self.game_id,
            phase=self.phase,
            player=PlayerView(name=player.name, hand=hand, score=player.score, is_dealer=player.is_dealer),
            opponent=OpponentView(name=opp.name, hand_count=opp_count, score=opp.score, is_dealer=opp.is_dealer),
            starter=self.starter,
            crib_count=len(self.crib),
            play_pile=self.play_pile,
            running_total=self.running_total,
            last_action=self.last_action,
            score_breakdown=self.score_breakdown,
            winner=self.winner,
            round_number=self.round_number,
            your_turn=your_turn,
        )
