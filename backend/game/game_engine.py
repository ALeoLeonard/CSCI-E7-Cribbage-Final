"""Core game engine — manages a single game as a state machine."""

from __future__ import annotations

import uuid

from .ai import BaseAI, create_ai
from .constants import WINNING_SCORE
from .deck import create_deck, deal, shuffle_deck
from .models import (
    AIDifficulty,
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
from .play_phase import can_play, process_play
from .scoring import calculate_score


class GameEngine:
    def __init__(self, player_name: str, ai_difficulty: AIDifficulty):
        self.game_id = str(uuid.uuid4())
        self.phase = GamePhase.DISCARD
        self.round_number = 1

        self.human = PlayerState(name=player_name)
        self.computer = PlayerState(name="Computer", is_dealer=True)
        # Human starts as non-dealer (computer deals first)

        self.ai: BaseAI = create_ai(ai_difficulty)
        self.ai_difficulty = ai_difficulty

        self.deck: list[Card] = []
        self.starter: Card | None = None
        self.crib: list[Card] = []

        # Play phase state
        self.play_pile: list[Card] = []
        self.running_total: int = 0
        self.human_play_hand: list[Card] = []
        self.computer_play_hand: list[Card] = []
        self.current_turn: str = ""  # "human" or "computer"
        self.last_go_by: str | None = None  # who said Go last

        self.last_action: LastAction | None = None
        self.action_log: list[LastAction] = []
        self.score_breakdown: ScoreBreakdown | None = None
        self.winner: str | None = None

        self._deal_round()

    @property
    def dealer(self) -> PlayerState:
        return self.human if self.human.is_dealer else self.computer

    @property
    def non_dealer(self) -> PlayerState:
        return self.computer if self.human.is_dealer else self.human

    def _log_action(self, action: LastAction) -> None:
        """Set last_action and append to action_log for the current API call."""
        self.last_action = action
        self.action_log.append(action)

    def _deal_round(self) -> None:
        """Shuffle, deal 6 to each, reset play state."""
        self.deck = shuffle_deck(create_deck())
        human_cards, self.deck = deal(self.deck, 6)
        computer_cards, self.deck = deal(self.deck, 6)
        self.human.hand = human_cards
        self.computer.hand = computer_cards
        self.crib = []
        self.starter = None
        self.play_pile = []
        self.running_total = 0
        self.last_go_by = None
        self.score_breakdown = None
        self.phase = GamePhase.DISCARD

        # Computer discards immediately
        ai_discard_indices = self.ai.choose_discards(
            self.computer.hand, self.computer.is_dealer
        )
        discarded = [self.computer.hand[i] for i in sorted(ai_discard_indices, reverse=True)]
        for i in sorted(ai_discard_indices, reverse=True):
            self.computer.hand.pop(i)
        self.crib.extend(discarded)

    def _check_winner(self) -> bool:
        if self.human.score >= WINNING_SCORE:
            self.winner = self.human.name
            self.phase = GamePhase.GAME_OVER
            return True
        if self.computer.score >= WINNING_SCORE:
            self.winner = self.computer.name
            self.phase = GamePhase.GAME_OVER
            return True
        return False

    def _add_score(self, player: PlayerState, points: int) -> None:
        player.score += points

    def discard(self, card_indices: list[int]) -> GameStateResponse:
        """Human discards 2 cards to crib."""
        self.action_log = []
        if self.phase != GamePhase.DISCARD:
            raise ValueError(f"Cannot discard in phase {self.phase}")
        if len(card_indices) != 2:
            raise ValueError("Must discard exactly 2 cards")
        if len(set(card_indices)) != 2:
            raise ValueError("Must discard 2 different cards")
        for i in card_indices:
            if i < 0 or i >= len(self.human.hand):
                raise ValueError(f"Invalid card index: {i}")

        discarded = [self.human.hand[i] for i in sorted(card_indices, reverse=True)]
        for i in sorted(card_indices, reverse=True):
            self.human.hand.pop(i)
        self.crib.extend(discarded)

        # Cut the starter
        starter_cards, self.deck = deal(self.deck, 1)
        self.starter = starter_cards[0]

        # Check for His Heels (Jack starter = 2 pts to dealer)
        if self.starter.rank == "J":
            self._add_score(self.dealer, 2)
            self._log_action(LastAction(
                actor=self.dealer.name,
                action="score",
                score_events=[ScoreEvent(player=self.dealer.name, points=2, reason="His Heels (Jack starter)")],
                message=f"{self.dealer.name} scores 2 for His Heels!",
            ))
            if self._check_winner():
                return self.get_state()

        # Set up play phase
        self.human_play_hand = self.human.hand.copy()
        self.computer_play_hand = self.computer.hand.copy()
        self.play_pile = []
        self.running_total = 0
        # Non-dealer plays first
        self.current_turn = "human" if not self.human.is_dealer else "computer"
        self.phase = GamePhase.PLAY

        # If computer goes first, auto-play
        if self.current_turn == "computer":
            self._computer_play_turn()

        return self.get_state()

    def play_card(self, card_index: int) -> GameStateResponse:
        """Human plays a card during pegging."""
        self.action_log = []
        if self.phase != GamePhase.PLAY:
            raise ValueError(f"Cannot play in phase {self.phase}")
        if self.current_turn != "human":
            raise ValueError("Not your turn")
        if card_index < 0 or card_index >= len(self.human_play_hand):
            raise ValueError(f"Invalid card index: {card_index}")

        card = self.human_play_hand[card_index]
        if card.value + self.running_total > 31:
            raise ValueError("That card would exceed 31")

        # Play the card
        self.human_play_hand.pop(card_index)
        self.play_pile.append(card)
        self.running_total += card.value

        # Score
        from .scoring import calculate_play_score
        events = calculate_play_score(self.play_pile, self.running_total)
        total_pts = sum(e.points for e in events)
        if total_pts > 0:
            self._add_score(self.human, total_pts)
            for e in events:
                e.player = self.human.name

        self._log_action(LastAction(
            actor=self.human.name,
            action="play",
            card=card,
            score_events=events,
            message=f"{self.human.name} plays {card.label}",
        ))

        if self.running_total == 31:
            self.play_pile = []
            self.running_total = 0
            self.last_go_by = None

        if self._check_winner():
            return self.get_state()

        # Check if play phase is over
        if not self.human_play_hand and not self.computer_play_hand:
            self._end_play_phase()
            return self.get_state()

        # Switch turn
        self.current_turn = "computer"
        self.last_go_by = None

        # Computer takes its turn(s)
        self._computer_play_turn()

        return self.get_state()

    def say_go(self) -> GameStateResponse:
        """Human says Go (can't play any card ≤ 31)."""
        self.action_log = []
        if self.phase != GamePhase.PLAY:
            raise ValueError(f"Cannot say go in phase {self.phase}")
        if self.current_turn != "human":
            raise ValueError("Not your turn")
        # Verify human really can't play
        if can_play(self.human_play_hand, self.running_total):
            raise ValueError("You have playable cards — you must play one")

        self._log_action(LastAction(
            actor=self.human.name,
            action="go",
            message=f"{self.human.name} says Go!",
        ))

        # Handle go logic
        self._handle_go("human")

        return self.get_state()

    def _handle_go(self, who_said_go: str) -> None:
        """Process a Go."""
        if self.last_go_by is not None and self.last_go_by != who_said_go:
            # Both said go — last card point, reset
            other = self.human if who_said_go == "computer" else self.computer
            self._add_score(other, 1)
            self._log_action(LastAction(
                actor=other.name,
                action="score",
                score_events=[ScoreEvent(player=other.name, points=1, reason="Go (last card)")],
                message=f"{other.name} scores 1 for Go",
            ))
            self.play_pile = []
            self.running_total = 0
            self.last_go_by = None
            if self._check_winner():
                return

            # Check if play phase is over
            if not self.human_play_hand and not self.computer_play_hand:
                self._end_play_phase()
                return

            # The person who said the first Go gets to lead
            if who_said_go == "human":
                self.current_turn = "human"
            else:
                self.current_turn = "computer"
                self._computer_play_turn()
        else:
            self.last_go_by = who_said_go
            # Other player continues
            if who_said_go == "human":
                self.current_turn = "computer"
                self._computer_play_turn()
            else:
                self.current_turn = "human"

    def _computer_play_turn(self) -> None:
        """Computer plays cards until it's human's turn or phase ends."""
        while self.current_turn == "computer" and self.phase == GamePhase.PLAY:
            if not self.computer_play_hand:
                if not self.human_play_hand:
                    self._end_play_phase()
                    return
                self.current_turn = "human"
                return

            idx = self.ai.choose_play(
                self.computer_play_hand, self.play_pile, self.running_total
            )

            if idx is None:
                # Computer says Go
                self._handle_go("computer")
                return

            card = self.computer_play_hand.pop(idx)
            self.play_pile.append(card)
            self.running_total += card.value

            from .scoring import calculate_play_score
            events = calculate_play_score(self.play_pile, self.running_total)
            total_pts = sum(e.points for e in events)
            if total_pts > 0:
                self._add_score(self.computer, total_pts)
                for e in events:
                    e.player = self.computer.name

            self._log_action(LastAction(
                actor=self.computer.name,
                action="play",
                card=card,
                score_events=events,
                message=f"Computer plays {card.label}",
            ))

            if self.running_total == 31:
                self.play_pile = []
                self.running_total = 0
                self.last_go_by = None

            if self._check_winner():
                return

            # Check if play phase done
            if not self.human_play_hand and not self.computer_play_hand:
                self._end_play_phase()
                return

            # If human has cards and can play, give them the turn
            if self.human_play_hand and can_play(self.human_play_hand, self.running_total):
                self.current_turn = "human"
                return

            # If human has cards but can't play, handle their Go automatically
            if self.human_play_hand and not can_play(self.human_play_hand, self.running_total):
                self._handle_go("human")
                # _handle_go may switch turns or continue computer loop
                continue

            # Human has no cards, computer continues
            if not self.human_play_hand and self.computer_play_hand:
                continue

    def _end_play_phase(self) -> None:
        """Award last card point and move to counting."""
        # Last card point (if total != 31, because 31 already scored)
        if self.running_total > 0 and self.running_total != 31:
            # Last person to play gets 1 point
            if self.play_pile:
                last_player = self.last_action.actor if self.last_action else self.non_dealer.name
                target = self.human if last_player == self.human.name else self.computer
                self._add_score(target, 1)
                if self._check_winner():
                    return

        self.play_pile = []
        self.running_total = 0
        self.phase = GamePhase.COUNT_NON_DEALER

    def acknowledge(self) -> GameStateResponse:
        """Advance through counting phases."""
        self.action_log = []
        if self.phase == GamePhase.COUNT_NON_DEALER:
            score, events = calculate_score(self.non_dealer.hand, self.starter)
            for e in events:
                e.player = self.non_dealer.name
            self._add_score(self.non_dealer, score)
            self.score_breakdown = ScoreBreakdown(
                hand=self.non_dealer.hand,
                starter=self.starter,
                items=events,
                total=score,
            )
            self._log_action(LastAction(
                actor=self.non_dealer.name,
                action="score",
                score_events=events,
                message=f"{self.non_dealer.name} scores {score} in hand",
            ))
            if self._check_winner():
                return self.get_state()
            self.phase = GamePhase.COUNT_DEALER

        elif self.phase == GamePhase.COUNT_DEALER:
            score, events = calculate_score(self.dealer.hand, self.starter)
            for e in events:
                e.player = self.dealer.name
            self._add_score(self.dealer, score)
            self.score_breakdown = ScoreBreakdown(
                hand=self.dealer.hand,
                starter=self.starter,
                items=events,
                total=score,
            )
            self._log_action(LastAction(
                actor=self.dealer.name,
                action="score",
                score_events=events,
                message=f"{self.dealer.name} scores {score} in hand",
            ))
            if self._check_winner():
                return self.get_state()
            self.phase = GamePhase.COUNT_CRIB

        elif self.phase == GamePhase.COUNT_CRIB:
            score, events = calculate_score(self.crib, self.starter)
            for e in events:
                e.player = self.dealer.name
            self._add_score(self.dealer, score)
            self.score_breakdown = ScoreBreakdown(
                hand=self.crib,
                starter=self.starter,
                items=events,
                total=score,
            )
            self._log_action(LastAction(
                actor=self.dealer.name,
                action="score",
                score_events=events,
                message=f"{self.dealer.name} scores {score} in crib",
            ))
            if self._check_winner():
                return self.get_state()

            # Start new round — swap dealer
            self.human.is_dealer = not self.human.is_dealer
            self.computer.is_dealer = not self.computer.is_dealer
            self.round_number += 1
            self._deal_round()
        else:
            raise ValueError(f"Cannot acknowledge in phase {self.phase}")

        return self.get_state()

    def get_state(self) -> GameStateResponse:
        """Build the client-visible game state."""
        # During play phase, show the play hand; otherwise the scoring hand
        if self.phase == GamePhase.PLAY:
            human_hand = self.human_play_hand
            opponent_count = len(self.computer_play_hand)
        else:
            human_hand = self.human.hand
            opponent_count = len(self.computer.hand)

        return GameStateResponse(
            game_id=self.game_id,
            phase=self.phase,
            player=PlayerView(
                name=self.human.name,
                hand=human_hand,
                score=self.human.score,
                is_dealer=self.human.is_dealer,
            ),
            opponent=OpponentView(
                name=self.computer.name,
                hand_count=opponent_count,
                score=self.computer.score,
                is_dealer=self.computer.is_dealer,
            ),
            starter=self.starter,
            crib_count=len(self.crib),
            play_pile=self.play_pile,
            running_total=self.running_total,
            last_action=self.last_action,
            action_log=self.action_log,
            score_breakdown=self.score_breakdown,
            winner=self.winner,
            round_number=self.round_number,
        )
