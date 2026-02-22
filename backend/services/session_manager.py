"""In-memory game session storage with TTL expiry."""

from __future__ import annotations

import time
from typing import Optional

from backend.config import settings
from backend.game.game_engine import GameEngine


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, GameEngine] = {}
        self._last_accessed: dict[str, float] = {}

    def create(self, engine: GameEngine) -> str:
        self._sessions[engine.game_id] = engine
        self._last_accessed[engine.game_id] = time.monotonic()
        return engine.game_id

    def get(self, game_id: str) -> Optional[GameEngine]:
        engine = self._sessions.get(game_id)
        if engine is None:
            return None
        elapsed = time.monotonic() - self._last_accessed.get(game_id, 0)
        if elapsed > settings.session_timeout_seconds:
            self.delete(game_id)
            return None
        self._last_accessed[game_id] = time.monotonic()
        return engine

    def delete(self, game_id: str) -> None:
        self._sessions.pop(game_id, None)
        self._last_accessed.pop(game_id, None)

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = time.monotonic()
        timeout = settings.session_timeout_seconds
        expired = [
            gid for gid, ts in self._last_accessed.items()
            if now - ts > timeout
        ]
        for gid in expired:
            self.delete(gid)
        return len(expired)

    @property
    def count(self) -> int:
        return len(self._sessions)


session_manager = SessionManager()
