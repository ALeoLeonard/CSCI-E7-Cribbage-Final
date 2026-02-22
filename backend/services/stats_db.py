"""SQLite persistence layer for game statistics."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

from backend.config import settings
from backend.game.models import DifficultyStats, PlayerStatsResponse, RecordGameRequest


class StatsDB:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.stats_db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    opponent_name TEXT NOT NULL,
                    player_score INTEGER NOT NULL,
                    opponent_score INTEGER NOT NULL,
                    won INTEGER NOT NULL,
                    ai_difficulty TEXT,
                    game_mode TEXT NOT NULL DEFAULT 'single',
                    hand_scores TEXT NOT NULL DEFAULT '[]',
                    crib_scores TEXT NOT NULL DEFAULT '[]',
                    highest_hand_score INTEGER NOT NULL DEFAULT 0,
                    total_points_scored INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def record_game(self, req: RecordGameRequest) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO game_results
                   (player_name, opponent_name, player_score, opponent_score, won,
                    ai_difficulty, game_mode, hand_scores, crib_scores,
                    highest_hand_score, total_points_scored, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    req.player_name,
                    req.opponent_name,
                    req.player_score,
                    req.opponent_score,
                    1 if req.won else 0,
                    req.ai_difficulty,
                    req.game_mode,
                    json.dumps(req.hand_scores),
                    json.dumps(req.crib_scores),
                    req.highest_hand_score,
                    req.total_points_scored,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def get_stats(self, player_name: str) -> PlayerStatsResponse:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM game_results
                   WHERE player_name = ?
                   ORDER BY created_at ASC""",
                (player_name,),
            ).fetchall()

        if not rows:
            return PlayerStatsResponse(
                player_name=player_name,
                games=0, wins=0, losses=0, win_rate=0.0,
                avg_hand_score=0.0, avg_crib_score=0.0,
                best_hand=0, total_points=0,
                current_streak=0, best_win_streak=0,
            )

        games = len(rows)
        wins = sum(1 for r in rows if r["won"])
        losses = games - wins

        all_hand_scores: list[int] = []
        all_crib_scores: list[int] = []
        best_hand = 0
        total_points = 0

        for r in rows:
            hs = json.loads(r["hand_scores"])
            cs = json.loads(r["crib_scores"])
            all_hand_scores.extend(hs)
            all_crib_scores.extend(cs)
            best_hand = max(best_hand, r["highest_hand_score"])
            total_points += r["total_points_scored"]

        avg_hand = sum(all_hand_scores) / len(all_hand_scores) if all_hand_scores else 0.0
        avg_crib = sum(all_crib_scores) / len(all_crib_scores) if all_crib_scores else 0.0

        # Calculate streaks
        current_streak = 0
        best_win_streak = 0
        streak = 0
        for r in rows:
            if r["won"]:
                streak = streak + 1 if streak > 0 else 1
                best_win_streak = max(best_win_streak, streak)
            else:
                streak = streak - 1 if streak < 0 else -1
            current_streak = streak

        # Per-difficulty breakdown
        diff_map: dict[str, dict[str, int]] = {}
        for r in rows:
            d = r["ai_difficulty"] or "multiplayer"
            if d not in diff_map:
                diff_map[d] = {"games": 0, "wins": 0}
            diff_map[d]["games"] += 1
            if r["won"]:
                diff_map[d]["wins"] += 1

        per_difficulty = [
            DifficultyStats(
                difficulty=d,
                games=v["games"],
                wins=v["wins"],
                losses=v["games"] - v["wins"],
                win_rate=round(v["wins"] / v["games"] * 100, 1) if v["games"] > 0 else 0.0,
            )
            for d, v in sorted(diff_map.items())
        ]

        return PlayerStatsResponse(
            player_name=player_name,
            games=games,
            wins=wins,
            losses=losses,
            win_rate=round(wins / games * 100, 1) if games > 0 else 0.0,
            avg_hand_score=round(avg_hand, 1),
            avg_crib_score=round(avg_crib, 1),
            best_hand=best_hand,
            total_points=total_points,
            current_streak=current_streak,
            best_win_streak=best_win_streak,
            per_difficulty=per_difficulty,
        )


stats_db = StatsDB()
