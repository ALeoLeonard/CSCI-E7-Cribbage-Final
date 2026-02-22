from __future__ import annotations

from fastapi import APIRouter

from backend.game.models import PlayerStatsResponse, RecordGameRequest
from backend.services.stats_db import stats_db

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.post("/record")
def record_game(req: RecordGameRequest) -> dict[str, str]:
    stats_db.record_game(req)
    return {"status": "ok"}


@router.get("/{player_name}", response_model=PlayerStatsResponse)
def get_stats(player_name: str) -> PlayerStatsResponse:
    return stats_db.get_stats(player_name)
