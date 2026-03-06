# Backend: FastAPI + statyczny frontend (Czesc 3)

## Cel

Backend dostarcza minimalne MVP do potwierdzenia:
- dzialajacej aplikacji FastAPI,
- serwowania statycznego frontendu Next.js (export) na `/`,
- dzialajacego endpointu API na `/api/health`.

## Struktura

- `app/main.py` - definicja aplikacji FastAPI i trasy HTTP.
- `app/frontend_dist/` - statyczny build frontendu kopiowany w Dockerze.
- `app/static/index.html` - fallback "hello world", gdy build frontendu nie jest dostepny.
- `pyproject.toml` - zaleznosci Pythona zarzadzane przez `uv`.

## Kontrakt API

- `GET /` - zwraca frontend Kanban z builda statycznego.
- `GET /api/health` - zwraca JSON potwierdzajacy stan backendu.

## Uwagi

- Na tym etapie backend nie zawiera logowania, bazy danych ani AI.
- Aplikacja ma pozostac prosta i latwa do uruchomienia w Dockerze.