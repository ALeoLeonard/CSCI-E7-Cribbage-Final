from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.game.game_engine import GameEngine
from backend.game.models import (
    DiscardRequest,
    GameStateResponse,
    NewGameRequest,
    PlayCardRequest,
)
from backend.services.session_manager import session_manager

router = APIRouter(prefix="/api/v1/game", tags=["game"])


@router.post("/new", response_model=GameStateResponse)
def new_game(req: NewGameRequest) -> GameStateResponse:
    engine = GameEngine(player_name=req.player_name, ai_difficulty=req.ai_difficulty)
    session_manager.create(engine)
    return engine.get_state()


@router.get("/{game_id}", response_model=GameStateResponse)
def get_game(game_id: str) -> GameStateResponse:
    engine = session_manager.get(game_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Game not found")
    return engine.get_state()


@router.post("/{game_id}/discard", response_model=GameStateResponse)
def discard(game_id: str, req: DiscardRequest) -> GameStateResponse:
    engine = session_manager.get(game_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return engine.discard(req.card_indices)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/play", response_model=GameStateResponse)
def play_card(game_id: str, req: PlayCardRequest) -> GameStateResponse:
    engine = session_manager.get(game_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return engine.play_card(req.card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/go", response_model=GameStateResponse)
def say_go(game_id: str) -> GameStateResponse:
    engine = session_manager.get(game_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return engine.say_go()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/acknowledge", response_model=GameStateResponse)
def acknowledge(game_id: str) -> GameStateResponse:
    engine = session_manager.get(game_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return engine.acknowledge()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
