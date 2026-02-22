"""WebSocket handler for multiplayer games."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from backend.game.multiplayer_engine import MultiplayerGameEngine
from backend.services.matchmaking import matchmaking


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}  # conn_id -> ws
        self._names: dict[str, str] = {}  # conn_id -> display name
        self._games: dict[str, MultiplayerGameEngine] = {}  # game_id -> engine
        self._player_game: dict[str, str] = {}  # conn_id -> game_id
        self._player_role: dict[str, str] = {}  # conn_id -> "player1"/"player2"
        self._conn_counter = 0

    def _next_id(self) -> str:
        self._conn_counter += 1
        return f"conn-{self._conn_counter}"

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        conn_id = self._next_id()
        self._connections[conn_id] = ws
        return conn_id

    async def disconnect(self, conn_id: str) -> None:
        self._connections.pop(conn_id, None)
        self._names.pop(conn_id, None)
        matchmaking.remove_from_queue(conn_id)
        matchmaking.cancel_private_game(conn_id)

        # Notify the other player in the game
        game_id = self._player_game.pop(conn_id, None)
        self._player_role.pop(conn_id, None)
        if game_id:
            for cid, gid in list(self._player_game.items()):
                if gid == game_id and cid != conn_id:
                    await self.send(cid, {"type": "opponent_disconnected", "message": "Your opponent has disconnected."})

    async def send(self, conn_id: str, data: dict) -> None:
        ws = self._connections.get(conn_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                pass

    async def _start_game(self, conn1: str, name1: str, conn2: str, name2: str) -> None:
        engine = MultiplayerGameEngine(name1, name2)
        game_id = engine.game_id
        self._games[game_id] = engine
        self._player_game[conn1] = game_id
        self._player_game[conn2] = game_id
        self._player_role[conn1] = "player1"
        self._player_role[conn2] = "player2"

        state1 = engine.get_state("player1").model_dump()
        state2 = engine.get_state("player2").model_dump()

        await self.send(conn1, {"type": "game_start", "state": state1})
        await self.send(conn2, {"type": "game_start", "state": state2})

    async def handle_message(self, conn_id: str, data: dict) -> None:
        msg_type = data.get("type")

        if msg_type == "quick_match":
            name = data.get("name", "Player")
            self._names[conn_id] = name
            match = matchmaking.add_to_queue(conn_id)
            if match:
                await self._start_game(match, self._names.get(match, "Player"), conn_id, name)
            else:
                await self.send(conn_id, {"type": "waiting", "message": "Waiting for opponent..."})

        elif msg_type == "create_private":
            name = data.get("name", "Player")
            self._names[conn_id] = name
            code = matchmaking.create_private_game(conn_id)
            await self.send(conn_id, {"type": "private_created", "code": code})

        elif msg_type == "join_private":
            code = data.get("code", "")
            name = data.get("name", "Player")
            self._names[conn_id] = name
            creator = matchmaking.join_private_game(code)
            if creator:
                await self._start_game(creator, self._names.get(creator, "Player"), conn_id, name)
            else:
                await self.send(conn_id, {"type": "error", "message": "Game not found"})

        elif msg_type == "discard":
            game_id = self._player_game.get(conn_id)
            role = self._player_role.get(conn_id)
            if not game_id or not role:
                return
            engine = self._games.get(game_id)
            if not engine:
                return
            try:
                engine.discard(role, data["card_indices"])
                await self._broadcast_state(game_id)
            except ValueError as e:
                await self.send(conn_id, {"type": "error", "message": str(e)})

        elif msg_type == "play_card":
            game_id = self._player_game.get(conn_id)
            role = self._player_role.get(conn_id)
            if not game_id or not role:
                return
            engine = self._games.get(game_id)
            if not engine:
                return
            try:
                engine.play_card(role, data["card_index"])
                await self._broadcast_state(game_id)
            except ValueError as e:
                await self.send(conn_id, {"type": "error", "message": str(e)})

        elif msg_type == "say_go":
            game_id = self._player_game.get(conn_id)
            role = self._player_role.get(conn_id)
            if not game_id or not role:
                return
            engine = self._games.get(game_id)
            if not engine:
                return
            try:
                engine.say_go(role)
                await self._broadcast_state(game_id)
            except ValueError as e:
                await self.send(conn_id, {"type": "error", "message": str(e)})

        elif msg_type == "acknowledge":
            game_id = self._player_game.get(conn_id)
            role = self._player_role.get(conn_id)
            if not game_id or not role:
                return
            engine = self._games.get(game_id)
            if not engine:
                return
            try:
                engine.acknowledge(role)
                await self._broadcast_state(game_id)
            except ValueError as e:
                await self.send(conn_id, {"type": "error", "message": str(e)})

        elif msg_type == "chat":
            game_id = self._player_game.get(conn_id)
            if not game_id:
                return
            # Broadcast chat to both
            for cid, gid in self._player_game.items():
                if gid == game_id and cid != conn_id:
                    await self.send(cid, {
                        "type": "chat",
                        "message": data.get("message", ""),
                    })

    async def _broadcast_state(self, game_id: str) -> None:
        engine = self._games.get(game_id)
        if not engine:
            return
        for conn_id, gid in self._player_game.items():
            if gid == game_id:
                role = self._player_role.get(conn_id)
                if role:
                    state = engine.get_state(role).model_dump()
                    await self.send(conn_id, {"type": "game_state", "state": state})


manager = ConnectionManager()
