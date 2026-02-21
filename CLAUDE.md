# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A mobile-first web implementation of the card game Cribbage, converted from the original Python CLI (`cribbage.py`) into a full-featured React + FastAPI application with single-player AI, multiplayer WebSocket support, animations, and sound effects.

## Running the Application

### Backend (FastAPI)
```bash
cd /Users/dcdz/Hacks/CSCI-E7-Cribbage-Final
python3 -m uvicorn backend.main:app --reload
```

### Frontend (Vite + React)
```bash
cd frontend
npm run dev
```
The Vite dev server proxies `/api` and `/ws` to `localhost:8000`.

### Tests
```bash
# From project root:
python3 -m pytest backend/tests/ -v
# Frontend type check:
cd frontend && npm run build
```

### Docker
```bash
docker compose up --build
# Frontend on :3000, Backend on :8000
```

## Architecture

### Backend (`backend/`)
- **`main.py`** — FastAPI app, CORS, routes
- **`config.py`** — Settings (pydantic-settings)
- **`game/`** — Core game logic:
  - `models.py` — Pydantic models (Card, GameState, phases, requests)
  - `constants.py` — SUIT_EMOJIS, RANK_ORDER, SUITS, RANKS
  - `deck.py` — create_deck, shuffle_deck, deal
  - `scoring.py` — Hand scoring (15s, pairs, runs, flush, nobs) + play-phase scoring (pairs, runs, 15, 31)
  - `game_engine.py` — Single-player state machine (DISCARD → PLAY → COUNT → rotate)
  - `multiplayer_engine.py` — Two-human state machine with per-player views
  - `ai.py` — Easy (random), Medium (evaluates discards), Hard (expected value over starters)
  - `play_phase.py` — Stateless pegging helpers
- **`api/`** — Route handlers:
  - `routes_game.py` — REST: POST /game/new, GET /game/{id}, POST /discard, /play, /go, /acknowledge
  - `routes_lobby.py` — WebSocket endpoint at /ws
  - `websocket_handler.py` — ConnectionManager for multiplayer
- **`services/`** — Session storage and matchmaking queue
- **`tests/`** — 29 pytest tests covering scoring, API, and full game flow

### Frontend (`frontend/`)
- **React + TypeScript + Vite + Tailwind CSS + Zustand**
- `src/api/` — REST client, WebSocket client, TypeScript types
- `src/store/` — gameStore (single-player), lobbyStore (multiplayer), soundStore
- `src/components/` — Card/, Board/, Game/, Lobby/, Layout/
- `src/hooks/` — useSound (Web Audio API synthesizer)
- `src/utils/` — cardUtils

## Key Design Decisions
- Opponent cards are **never** sent to the frontend (only `hand_count`)
- Computer responds immediately in single-player (backend calculates AI move in same request)
- Sound effects use Web Audio API synthesis — no audio files needed
- State machine phases: DISCARD → PLAY → COUNT_NON_DEALER → COUNT_DEALER → COUNT_CRIB → rotate

## Original CLI Game
The original single-file game is preserved at `cribbage.py` and can still be run:
```bash
python cribbage.py
```
