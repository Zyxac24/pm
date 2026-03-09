# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban Board MVP with AI-powered board manipulation. Full-stack: Next.js frontend (static export) + FastAPI backend + SQLite + OpenRouter AI.

## Commands

### Backend (`backend/`)
```bash
uv pip install .          # Install dependencies
uvicorn app.main:app --reload  # Dev server (port 8000)
pytest                    # Run tests
pytest --cov              # With coverage
pytest tests/test_main_api.py  # Single test file
```

### Frontend (`frontend/`)
```bash
npm install
npm run dev               # Dev server (port 3000)
npm run build             # Static export to ./out/
npm run lint
npm run test:unit         # Vitest unit tests
npm run test:e2e          # Playwright E2E tests
npm run test:all
npx vitest run src/lib/auth.test.ts  # Single unit test file
```

### Docker (full stack)
```bash
docker compose up --build  # Build and run at http://localhost:8000
docker compose down
scripts/start-linux.sh     # Quick start
```

## Architecture

### Data Flow
1. Frontend (Next.js static export) is built into `frontend/out/`
2. FastAPI serves the frontend statically from `backend/app/frontend_dist/`
3. In Docker, the multi-stage build copies `frontend/out` → `backend/app/frontend_dist`
4. For local frontend dev, the frontend talks to backend at `localhost:8000`

### Backend Modules (`backend/app/`)
- `main.py` — FastAPI routes and app lifecycle (serves frontend + API)
- `db.py` — SQLite repository pattern; tables: `users`, `kanban_boards` (board stored as JSON blob)
- `models.py` — Pydantic models for all API payloads
- `ai_client.py` — OpenRouter API integration with Structured Outputs
- `kanban_patch.py` — Applies AI-generated patches (add/move/delete cards) to board state

### API Endpoints
```
GET  /api/health
GET  /api/kanban/{username}       # Fetch user's board
PUT  /api/kanban/{username}       # Save board state
POST /api/ai/test                 # Test OpenRouter connectivity
POST /api/ai/chat/{username}      # AI chat; returns message + optional patch
```

### Frontend Components (`frontend/src/`)
- `components/AuthGate.tsx` — Login screen (hardcoded credentials)
- `components/KanbanBoard.tsx` — Main state management
- `components/KanbanColumn.tsx` — Column with dnd-kit drag-drop
- `components/KanbanCard.tsx` — Individual card
- `components/AiSidebarChat.tsx` — AI chat panel
- `lib/kanbanApi.ts` — API client functions
- `lib/auth.ts` — Authentication (localStorage token)

### Authentication
Frontend-only auth: token stored in localStorage. Backend does not verify tokens — all boards are accessed by username from the URL path.

## Key Decisions
- Board state is a single JSON blob in SQLite (column order and card order preserved in JSON)
- AI responses use OpenRouter's Structured Outputs (JSON schema enforced)
- Frontend is statically exported (no SSR); Next.js App Router used
- Package manager: `uv` for Python, `npm` for Node

## Environment
`.env` in root: `OPENROUTER_API_KEY=...`

## Design Colors
- Yellow accent: `#ecad0a`
- Main blue: `#209dd7`
- Secondary purple: `#753991`
- Dark navy: `#032147`
