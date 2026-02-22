"""Tests for game statistics recording and retrieval."""

import pytest

from backend.game.models import RecordGameRequest
from backend.services.stats_db import StatsDB


@pytest.fixture
def db(tmp_path):
    return StatsDB(db_path=str(tmp_path / "test_stats.db"))


def _make_result(**overrides) -> RecordGameRequest:
    defaults = dict(
        player_name="Alice",
        opponent_name="Computer",
        player_score=121,
        opponent_score=95,
        won=True,
        ai_difficulty="easy",
        game_mode="single",
        hand_scores=[4, 8, 12],
        crib_scores=[6, 2],
        highest_hand_score=12,
        total_points_scored=121,
    )
    defaults.update(overrides)
    return RecordGameRequest(**defaults)


def test_record_and_retrieve(db):
    db.record_game(_make_result())
    stats = db.get_stats("Alice")
    assert stats.games == 1
    assert stats.wins == 1
    assert stats.losses == 0
    assert stats.win_rate == 100.0
    assert stats.avg_hand_score == 8.0  # (4+8+12)/3
    assert stats.avg_crib_score == 4.0  # (6+2)/2
    assert stats.best_hand == 12
    assert stats.total_points == 121
    assert stats.current_streak == 1
    assert stats.best_win_streak == 1


def test_zero_game_player(db):
    stats = db.get_stats("Nobody")
    assert stats.games == 0
    assert stats.wins == 0
    assert stats.win_rate == 0.0
    assert stats.avg_hand_score == 0.0
    assert stats.current_streak == 0
    assert stats.best_win_streak == 0


def test_win_streak_calculation(db):
    # Win 3 in a row
    for _ in range(3):
        db.record_game(_make_result(won=True))
    stats = db.get_stats("Alice")
    assert stats.current_streak == 3
    assert stats.best_win_streak == 3

    # Then lose 2
    for _ in range(2):
        db.record_game(_make_result(won=False, player_score=90, opponent_score=121))
    stats = db.get_stats("Alice")
    assert stats.current_streak == -2
    assert stats.best_win_streak == 3


def test_per_difficulty_breakdown(db):
    db.record_game(_make_result(ai_difficulty="easy", won=True))
    db.record_game(_make_result(ai_difficulty="easy", won=False, player_score=90, opponent_score=121))
    db.record_game(_make_result(ai_difficulty="hard", won=True))

    stats = db.get_stats("Alice")
    assert len(stats.per_difficulty) == 2
    easy = next(d for d in stats.per_difficulty if d.difficulty == "easy")
    assert easy.games == 2
    assert easy.wins == 1
    assert easy.win_rate == 50.0
    hard = next(d for d in stats.per_difficulty if d.difficulty == "hard")
    assert hard.games == 1
    assert hard.wins == 1


def test_multiple_games_averages(db):
    db.record_game(_make_result(hand_scores=[10, 20], crib_scores=[5], highest_hand_score=20, total_points_scored=121))
    db.record_game(_make_result(hand_scores=[6], crib_scores=[3], highest_hand_score=6, total_points_scored=90, won=False, player_score=90, opponent_score=121))

    stats = db.get_stats("Alice")
    assert stats.games == 2
    assert stats.wins == 1
    assert stats.losses == 1
    assert stats.win_rate == 50.0
    # avg_hand = (10+20+6)/3 = 12.0
    assert stats.avg_hand_score == 12.0
    # avg_crib = (5+3)/2 = 4.0
    assert stats.avg_crib_score == 4.0
    assert stats.best_hand == 20
    assert stats.total_points == 211  # 121 + 90
