import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as ApiPath, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.status import HTTP_404_NOT_FOUND, HTTP_429_TOO_MANY_REQUESTS

from app.ai_client import (
    AI_TEST_PROMPT,
    OPENROUTER_MODEL,
    OpenRouterConfigError,
    OpenRouterRequestError,
    OpenRouterSchemaError,
    run_connectivity_test,
    run_structured_kanban_chat,
)
from app.db import KanbanRepository, UserNotFoundError
from app.kanban_patch import AiPatchError, apply_ai_patch
from app.models import AiChatRequestModel, AiChatResponseModel, AiTestResponseModel, BoardModel

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST_PATH = BASE_DIR / "frontend_dist"
FALLBACK_INDEX_PATH = BASE_DIR / "static" / "index.html"
DEFAULT_DB_PATH = BASE_DIR.parent / "data" / "kanban.db"

_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60  # seconds

USERNAME_PATTERN = r"^[a-z0-9_-]{1,32}$"
UsernameParam = Annotated[str, ApiPath(pattern=USERNAME_PATTERN)]

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def _resolve_db_path() -> Path:
    raw_value = os.getenv("KANBAN_DB_PATH")
    if raw_value:
        return Path(raw_value)
    return DEFAULT_DB_PATH


def create_app() -> FastAPI:
    repository = KanbanRepository(db_path=_resolve_db_path())
    rate_store: dict[str, list[float]] = defaultdict(list)

    def _check_rate_limit(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - _RATE_LIMIT_WINDOW
        rate_store[client_ip] = [t for t in rate_store[client_ip] if t > window_start]
        if len(rate_store[client_ip]) >= _RATE_LIMIT_MAX:
            logger.warning("Rate limit exceeded for client %s", client_ip)
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many AI requests. Please wait before trying again.",
            )
        rate_store[client_ip].append(now)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.initialize()
        app.state.repository = repository
        yield

    app = FastAPI(title="Kanban MVP Backend", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type"],
    )

    @app.get("/")
    def read_index() -> FileResponse:
        return _serve_frontend_path("")

    @app.get("/api/health")
    def read_health() -> dict[str, str]:
        return {"status": "ok", "service": "backend"}

    @app.post("/api/ai/test", response_model=AiTestResponseModel)
    def test_openrouter_connection(request: Request) -> AiTestResponseModel:
        _check_rate_limit(request)
        try:
            answer = run_connectivity_test(prompt=AI_TEST_PROMPT)
        except OpenRouterConfigError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
        except OpenRouterRequestError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

        return AiTestResponseModel(
            provider="openrouter",
            model=OPENROUTER_MODEL,
            prompt=AI_TEST_PROMPT,
            answer=answer,
        )

    @app.post("/api/ai/chat/{username}", response_model=AiChatResponseModel)
    def chat_with_ai(
        username: UsernameParam, payload: AiChatRequestModel, request: Request
    ) -> AiChatResponseModel:
        _check_rate_limit(request)

        try:
            board_data = app.state.repository.get_board(username)
        except UserNotFoundError as error:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

        try:
            ai_response = run_structured_kanban_chat(
                board=board_data,
                question=payload.question,
                history=payload.history,
            )
        except OpenRouterConfigError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
        except OpenRouterSchemaError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        except OpenRouterRequestError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

        next_board = board_data
        patch_applied = False
        if ai_response.patch is not None:
            try:
                next_board = apply_ai_patch(board=board_data, patch=ai_response.patch)
                next_board = app.state.repository.update_board(
                    username=username,
                    board=next_board,
                )
                patch_applied = True
                logger.info("AI patch applied for user %s", username)
            except AiPatchError as error:
                logger.warning("AI patch rejected for user %s: %s", username, error)
                next_board = board_data
            except UserNotFoundError as error:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=str(error),
                ) from error

        return AiChatResponseModel(
            message=ai_response.message,
            patchApplied=patch_applied,
            board=BoardModel.model_validate(next_board),
        )

    @app.get("/api/kanban/{username}", response_model=BoardModel)
    def read_kanban_board(username: UsernameParam) -> BoardModel:
        try:
            board_data = app.state.repository.get_board(username)
        except UserNotFoundError as error:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        return BoardModel.model_validate(board_data)

    @app.put("/api/kanban/{username}", response_model=BoardModel)
    def update_kanban_board(username: UsernameParam, payload: BoardModel) -> BoardModel:
        try:
            updated_board = app.state.repository.update_board(
                username=username,
                board=payload.model_dump(mode="json"),
            )
        except UserNotFoundError as error:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        return BoardModel.model_validate(updated_board)

    @app.get("/{full_path:path}")
    def read_frontend(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Not found.")
        return _serve_frontend_path(full_path)

    return app


app = create_app()


def _serve_frontend_path(path: str) -> FileResponse:
    if not FRONTEND_DIST_PATH.exists():
        return FileResponse(FALLBACK_INDEX_PATH)

    if path:
        target = FRONTEND_DIST_PATH / path
        if target.is_file():
            return FileResponse(target)

    return FileResponse(FRONTEND_DIST_PATH / "index.html")
