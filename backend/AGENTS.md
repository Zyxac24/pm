# Backend: FastAPI + SQLite + API Kanban (Czesc 6)

## Cel

Backend dostarcza MVP do potwierdzenia:
- dzialajacej aplikacji FastAPI,
- serwowania statycznego frontendu Next.js (export) na `/`,
- dzialajacego endpointu API na `/api/health`,
- endpointow odczytu i zapisu tablicy Kanban dla wskazanego uzytkownika.

## Struktura

- `app/main.py` - definicja aplikacji FastAPI i trasy HTTP.
- `app/db.py` - inicjalizacja SQLite, seed danych i operacje repozytorium.
- `app/models.py` - modele i walidacja payloadu tablicy Kanban.
- `app/frontend_dist/` - statyczny build frontendu kopiowany w Dockerze.
- `app/static/index.html` - fallback "hello world", gdy build frontendu nie jest dostepny.
- `pyproject.toml` - zaleznosci Pythona zarzadzane przez `uv`.
- `tests/` - testy backendu (repozytorium + walidacja modeli).

## Kontrakt API

- `GET /` - zwraca frontend Kanban z builda statycznego.
- `GET /api/health` - zwraca JSON potwierdzajacy stan backendu.
- `GET /api/kanban/{username}` - zwraca tablice Kanban uzytkownika.
- `PUT /api/kanban/{username}` - zapisuje tablice Kanban uzytkownika po walidacji payloadu.

## Uwagi

- Baza SQLite tworzona jest automatycznie, jesli nie istnieje.
- Domyslnie seedowany jest uzytkownik `user` z poczatkowa tablica.
- W Dockerze katalog danych jest mapowany przez volume, aby zachowac stan po restarcie kontenera.
- Logowanie nadal nie jest backendowo zabezpieczone (to bedzie rozwijane pozniej).
- Aplikacja ma pozostac prosta i latwa do uruchomienia w Dockerze.