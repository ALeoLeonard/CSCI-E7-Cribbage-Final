# Cribbage Game

A full-featured web implementation of the classic card game Cribbage, built as a React + FastAPI application with single-player AI, multiplayer WebSocket support, animations, and sound effects.

Originally created as Andy Leonard's **CSCI E-7** final project, converted from a Python CLI game into a modern web app.

## Features

- Complete Cribbage rules: 15s, pairs, runs, flushes, nobs, pegging, crib scoring
- Three AI difficulty levels (Easy, Medium, Hard)
- Multiplayer via WebSocket matchmaking
- Split-screen layout with S-shaped cribbage board and fanned card play areas
- Web Audio API sound effects (card taps, plays, shuffles, scoring)
- Computer thinking delay for natural play pacing
- Animated card dealing, playing, and score floating

## Quick Start

### Option 1: Local Development

**Backend** (Python 3.10+):
```bash
pip install -r backend/requirements.txt
python3 -m uvicorn backend.main:app --reload
```

**Frontend** (Node 18+):
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies `/api` and `/ws` to the backend on port 8000.

### Option 2: Docker

```bash
docker compose up --build
```

Frontend on http://localhost:3000, Backend on http://localhost:8000.

## Architecture

```
├── backend/                  # FastAPI (Python)
│   ├── main.py               # App entry, CORS, routes
│   ├── game/                 # Core game logic
│   │   ├── game_engine.py    # Single-player state machine
│   │   ├── multiplayer_engine.py  # Two-human state machine
│   │   ├── scoring.py        # Hand + play-phase scoring
│   │   ├── ai.py             # Easy/Medium/Hard AI
│   │   └── ...
│   ├── api/                  # REST + WebSocket handlers
│   ├── services/             # Session storage, matchmaking
│   └── tests/                # 29 pytest tests
├── frontend/                 # React + TypeScript + Vite
│   └── src/
│       ├── components/       # Board, Card, Game, Layout, Lobby
│       ├── store/            # Zustand stores (game, lobby, sound)
│       ├── hooks/            # useSound (Web Audio synthesizer)
│       └── api/              # REST client, WebSocket client
└── docker-compose.yml
```

## How to Play

1. **Objective**: First to 121 points wins
2. **Discard**: Each player is dealt 6 cards and discards 2 to the dealer's crib
3. **Play (Pegging)**: Alternate playing cards — score for 15s, 31s, pairs, and runs
4. **Count**: Score hands and crib for 15s, pairs, runs, flushes, and nobs
5. **Repeat**: Dealer alternates each round until someone reaches 121

## Tests

```bash
# Backend
python3 -m pytest backend/tests/ -v

# Frontend type check
cd frontend && npm run build
```

## Original CLI Game

The original single-file Python game is preserved at `cribbage.py`:
```bash
python cribbage.py
```
