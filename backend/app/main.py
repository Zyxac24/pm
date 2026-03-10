import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path as ApiPath, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_429_TOO_MANY_REQUESTS,
)

from app.ai_client import (
    AI_TEST_PROMPT,
    OPENROUTER_MODEL,
    OpenRouterConfigError,
    OpenRouterRequestError,
    OpenRouterSchemaError,
    run_connectivity_test,
    run_structured_kanban_chat,
)
from app.auth import AuthError, create_access_token, decode_access_token
from app.db import (
    BoardAccessDeniedError,
    BoardNotFoundError,
    InvalidCredentialsError,
    KanbanRepository,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.kanban_patch import AiPatchError, apply_ai_patch
from app.models import (
    AiChatRequestModel,
    AiChatResponseModel,
    AiTestResponseModel,
    BoardCreateRequest,
    BoardDetailResponse,
    BoardListResponse,
    BoardModel,
    BoardSummaryResponse,
    BoardUpdateMetaRequest,
    FlexibleBoardModel,
    UserLoginRequest,
    UserLoginResponse,
    UserProfileResponse,
    UserRegisterRequest,
)

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

bearer_scheme = HTTPBearer(auto_error=False)


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

    def _get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    ) -> dict:
        if credentials is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        try:
            payload = decode_access_token(credentials.credentials)
            user_id = int(payload["sub"])
            username = payload["username"]
            return {"user_id": user_id, "username": username}
        except AuthError as error:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=str(error),
            ) from error

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.initialize()
        app.state.repository = repository
        yield

    app = FastAPI(title="Kanban Project Manager", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # --- Frontend serving ---

    @app.get("/")
    def read_index() -> FileResponse:
        return _serve_frontend_path("")

    # --- Health ---

    @app.get("/api/health")
    def read_health() -> dict[str, str]:
        return {"status": "ok", "service": "backend"}

    # --- Auth endpoints ---

    @app.post("/api/auth/register", response_model=UserLoginResponse)
    def register_user(payload: UserRegisterRequest) -> UserLoginResponse:
        try:
            user_data = repository.create_user(
                username=payload.username,
                password=payload.password,
            )
        except UserAlreadyExistsError as error:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

        token = create_access_token(user_data["user_id"], user_data["username"])
        return UserLoginResponse(
            token=token,
            username=user_data["username"],
            user_id=user_data["user_id"],
        )

    @app.post("/api/auth/login", response_model=UserLoginResponse)
    def login_user(payload: UserLoginRequest) -> UserLoginResponse:
        try:
            user_data = repository.authenticate_user(
                username=payload.username,
                password=payload.password,
            )
        except InvalidCredentialsError as error:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=str(error),
            ) from error

        token = create_access_token(user_data["user_id"], user_data["username"])
        return UserLoginResponse(
            token=token,
            username=user_data["username"],
            user_id=user_data["user_id"],
        )

    @app.get("/api/auth/me", response_model=UserProfileResponse)
    def get_current_user_profile(
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> UserProfileResponse:
        try:
            user_data = repository.get_user_by_id(current_user["user_id"])
        except UserNotFoundError as error:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        return UserProfileResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            created_at=user_data["created_at"],
        )

    # --- Board management endpoints ---

    @app.get("/api/boards", response_model=BoardListResponse)
    def list_user_boards(
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> BoardListResponse:
        boards = repository.list_boards(current_user["user_id"])
        return BoardListResponse(
            boards=[BoardSummaryResponse(**b) for b in boards]
        )

    @app.post("/api/boards", response_model=BoardDetailResponse, status_code=201)
    def create_board(
        payload: BoardCreateRequest,
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> BoardDetailResponse:
        result = repository.create_board(
            user_id=current_user["user_id"],
            name=payload.name,
            description=payload.description,
        )
        return BoardDetailResponse(
            board_id=result["board_id"],
            name=result["name"],
            description=result["description"],
            board=FlexibleBoardModel.model_validate(result["board"]),
        )

    @app.get("/api/boards/{board_id}", response_model=BoardDetailResponse)
    def get_board(
        board_id: int,
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> BoardDetailResponse:
        try:
            result = repository.get_board_by_id(board_id, current_user["user_id"])
        except BoardNotFoundError as error:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(error)) from error
        except BoardAccessDeniedError as error:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(error)) from error

        return BoardDetailResponse(
            board_id=result["board_id"],
            name=result["name"],
            description=result["description"],
            board=FlexibleBoardModel.model_validate(result["board"]),
        )

    @app.put("/api/boards/{board_id}", response_model=BoardDetailResponse)
    def update_board_data(
        board_id: int,
        payload: FlexibleBoardModel,
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> BoardDetailResponse:
        try:
            result = repository.update_board_data(
                board_id=board_id,
                user_id=current_user["user_id"],
                board=payload.model_dump(mode="json"),
            )
        except BoardNotFoundError as error:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(error)) from error
        except BoardAccessDeniedError as error:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(error)) from error

        return BoardDetailResponse(
            board_id=result["board_id"],
            name=result["name"],
            description=result["description"],
            board=FlexibleBoardModel.model_validate(result["board"]),
        )

    @app.patch("/api/boards/{board_id}/meta", response_model=BoardSummaryResponse)
    def update_board_meta(
        board_id: int,
        payload: BoardUpdateMetaRequest,
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> BoardSummaryResponse:
        try:
            result = repository.update_board_meta(
                board_id=board_id,
                user_id=current_user["user_id"],
                name=payload.name,
                description=payload.description,
            )
        except BoardNotFoundError as error:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(error)) from error
        except BoardAccessDeniedError as error:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(error)) from error

        return BoardSummaryResponse(**result)

    @app.delete("/api/boards/{board_id}", status_code=204)
    def delete_board(
        board_id: int,
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> None:
        try:
            repository.delete_board(board_id, current_user["user_id"])
        except BoardNotFoundError as error:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(error)) from error
        except BoardAccessDeniedError as error:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(error)) from error

    # --- AI endpoints ---

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

    @app.post("/api/ai/chat/{board_id}", response_model=AiChatResponseModel)
    def chat_with_ai_for_board(
        board_id: int,
        payload: AiChatRequestModel,
        request: Request,
        current_user: Annotated[dict, Depends(_get_current_user)],
    ) -> AiChatResponseModel:
        _check_rate_limit(request)

        try:
            board_result = repository.get_board_by_id(board_id, current_user["user_id"])
        except BoardNotFoundError as error:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(error)) from error
        except BoardAccessDeniedError as error:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(error)) from error

        board_data = board_result["board"]

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
                repository.update_board_data(
                    board_id=board_id,
                    user_id=current_user["user_id"],
                    board=next_board,
                )
                patch_applied = True
                logger.info("AI patch applied for board %d", board_id)
            except AiPatchError as error:
                logger.warning("AI patch rejected for board %d: %s", board_id, error)
                next_board = board_data
            except (BoardNotFoundError, BoardAccessDeniedError) as error:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(error)) from error

        return AiChatResponseModel(
            message=ai_response.message,
            patchApplied=patch_applied,
            board=FlexibleBoardModel.model_validate(next_board),
        )

    # --- Legacy endpoints (backward compat) ---

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

    @app.post("/api/ai/chat/legacy/{username}", response_model=AiChatResponseModel)
    def chat_with_ai_legacy(
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
            board=FlexibleBoardModel.model_validate(next_board),
        )

    # --- Frontend catch-all ---

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
