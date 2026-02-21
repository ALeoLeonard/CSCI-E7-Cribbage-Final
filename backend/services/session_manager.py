"""In-memory game session storage."""

from __future__ import annotations

from typing import Optional

from backend.game.game_engine import GameEngine


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, GameEngine] = {}

    def create(self, engine: GameEngine) -> str:
        self._sessions[engine.game_id] = engine
        return engine.game_id

    def get(self, game_id: str) -> Optional[GameEngine]:
        return self._sessions.get(game_id)

    def delete(self, game_id: str) -> None:
        self._sessions.pop(game_id, None)

    @property
    def count(self) -> int:
        return len(self._sessions)


session_manager = SessionManager()
