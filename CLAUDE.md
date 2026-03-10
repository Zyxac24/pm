# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban Project Manager with AI-powered board manipulation. Full-stack: Next.js frontend (static export) + FastAPI backend + SQLite + OpenRouter AI. Features user management with JWT auth, multiple boards per user, and flexible column configurations.

## Commands

### Backend (`backend/`)
```bash
uv pip install -e .       # Install dependencies (editable)
uvicorn app.main:app --reload  # Dev server (port 8000)
pytest                    # Run tests
pytest --cov=app          # With coverage
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
- `db.py` — SQLite repository pattern; tables: `users`, `kanban_boards`; supports multi-board per user
- `models.py` — Pydantic models for all API payloads (BoardModel for legacy fixed columns, FlexibleBoardModel for new boards)
- `auth.py` — JWT token creation/verification, bcrypt password hashing
- `ai_client.py` — OpenRouter API integration with Structured Outputs
- `kanban_patch.py` — Applies AI-generated patches (add/move/delete cards) to board state

### API Endpoints
```
# Health
GET  /api/health

# Auth
POST /api/auth/register          # Register new user (returns JWT)
POST /api/auth/login             # Login (returns JWT)
GET  /api/auth/me                # Get current user profile (requires JWT)

# Board Management (requires JWT)
GET  /api/boards                 # List user's boards
POST /api/boards                 # Create new board
GET  /api/boards/{board_id}      # Get board by ID
PUT  /api/boards/{board_id}      # Update board data
PATCH /api/boards/{board_id}/meta # Update board name/description
DELETE /api/boards/{board_id}    # Delete board

# AI (requires JWT for board endpoints)
POST /api/ai/test                # Test OpenRouter connectivity
POST /api/ai/chat/{board_id}     # AI chat for specific board (requires JWT)

# Legacy (no auth required, backward compat)
GET  /api/kanban/{username}      # Fetch user's first board
PUT  /api/kanban/{username}      # Save board state
POST /api/ai/chat/legacy/{username} # AI chat via username
```

### Frontend Components (`frontend/src/`)
- `components/AuthGate.tsx` — Login/Register screen with JWT auth
- `components/BoardSelector.tsx` — Board list, create, delete
- `components/KanbanBoard.tsx` — Main board state management (takes boardId prop)
- `components/KanbanColumn.tsx` — Column with dnd-kit drag-drop
- `components/KanbanCard.tsx` — Individual card
- `components/AiSidebarChat.tsx` — AI chat panel
- `lib/auth.ts` — JWT auth utilities, session management
- `lib/boardsApi.ts` — Board CRUD API client
- `lib/kanbanApi.ts` — Legacy board API client
- `lib/aiChatApi.ts` — AI chat API client (supports both board ID and legacy)

### Authentication
- Backend: JWT tokens with bcrypt password hashing
- Registration creates a default board for new users
- Demo user: `user` / `password` (created on DB init)
- Legacy endpoints remain unauthenticated for backward compatibility

### Database Schema
```sql
users: id, username (UNIQUE), password_hash, created_at
kanban_boards: id, user_id (FK), name, description, board_json, updated_at, version
```

## Key Decisions
- Board state is a JSON blob in SQLite (column order and card order preserved)
- New boards use FlexibleBoardModel (1-20 custom columns); legacy boards use BoardModel (5 fixed columns)
- AI responses use OpenRouter's Structured Outputs (JSON schema enforced)
- Frontend is statically exported (no SSR); Next.js App Router used
- Package manager: `uv` for Python, `npm` for Node
- Auth: JWT + bcrypt (PyJWT, bcrypt packages)

## Environment
`.env` in root: `OPENROUTER_API_KEY=...`
Optional: `JWT_SECRET_KEY=...` (defaults to dev secret)

## Design Colors
- Yellow accent: `#ecad0a`
- Main blue: `#209dd7`
- Secondary purple: `#753991`
- Dark navy: `#032147`
