from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="Kanban MVP Backend")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST_PATH = BASE_DIR / "frontend_dist"
FALLBACK_INDEX_PATH = BASE_DIR / "static" / "index.html"


@app.get("/")
def read_index() -> FileResponse:
    return _serve_frontend_path("")


@app.get("/api/health")
def read_health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/{full_path:path}")
def read_frontend(full_path: str) -> FileResponse:
    return _serve_frontend_path(full_path)


def _serve_frontend_path(path: str) -> FileResponse:
    if not FRONTEND_DIST_PATH.exists():
        return FileResponse(FALLBACK_INDEX_PATH)

    if path:
        target = FRONTEND_DIST_PATH / path
        if target.is_file():
            return FileResponse(target)

    return FileResponse(FRONTEND_DIST_PATH / "index.html")
