"""Queue-based matchmaking and private game code generation."""

from __future__ import annotations

import random
import string
from collections import deque
from typing import Optional


def generate_join_code() -> str:
    """Generate a 6-character alphanumeric join code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class MatchmakingQueue:
    def __init__(self) -> None:
        self._queue: deque[str] = deque()  # player connection IDs
        self._private_games: dict[str, str] = {}  # join_code -> creator connection ID

    def add_to_queue(self, connection_id: str) -> Optional[str]:
        """
        Add player to quick-match queue.
        Returns the other player's connection_id if a match is found, None otherwise.
        """
        if self._queue:
            other = self._queue.popleft()
            if other != connection_id:
                return other
        self._queue.append(connection_id)
        return None

    def remove_from_queue(self, connection_id: str) -> None:
        try:
            self._queue.remove(connection_id)
        except ValueError:
            pass

    def create_private_game(self, connection_id: str) -> str:
        """Create a private game and return the join code."""
        code = generate_join_code()
        self._private_games[code] = connection_id
        return code

    def join_private_game(self, code: str) -> Optional[str]:
        """Join a private game. Returns creator's connection_id or None."""
        return self._private_games.pop(code.upper(), None)

    def cancel_private_game(self, connection_id: str) -> None:
        """Cancel a private game by the creator."""
        to_remove = [k for k, v in self._private_games.items() if v == connection_id]
        for k in to_remove:
            del self._private_games[k]


matchmaking = MatchmakingQueue()
