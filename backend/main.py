from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_game import router as game_router
from backend.api.routes_lobby import router as lobby_router
from backend.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(lobby_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
