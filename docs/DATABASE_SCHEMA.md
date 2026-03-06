# Czesc 5: Proponowany schemat bazy danych (SQLite + JSON)

## Cel

Ten dokument opisuje propozycje modelu danych dla Kanbana:
- SQLite jako lokalna baza,
- wsparcie wielu uzytkownikow w modelu danych,
- w MVP jedna tablica Kanban na uzytkownika,
- stan tablicy przechowywany jako JSON.

## Zalozenia MVP

- Logowanie demo: `user` / `password` (na razie bez pelnej auth backendowej).
- Jeden rekord tablicy Kanban na jednego uzytkownika.
- Backend tworzy baze i tabele automatycznie, jesli nie istnieja.
- Dane tablicy zapisujemy atomowo jako jeden JSON (snapshot).

## Model relacyjny (propozycja)

### Tabela `users`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT NOT NULL UNIQUE
- `created_at` TEXT NOT NULL (ISO timestamp)

Rola:
- przygotowanie pod wielu uzytkownikow,
- stabilny klucz `id` do relacji z tablica.

### Tabela `kanban_boards`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `board_json` TEXT NOT NULL CHECK(json_valid(board_json))
- `updated_at` TEXT NOT NULL (ISO timestamp)
- `version` INTEGER NOT NULL DEFAULT 1

Rola:
- jedna tablica na uzytkownika (UNIQUE `user_id`),
- caly stan tablicy trzymany jako JSON,
- `version` pod przyszla kontrola wspolbieznosci (opcjonalna na MVP).

## SQL DDL (proponowane)

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kanban_boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  updated_at TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_boards_user_id ON kanban_boards(user_id);
```

## Struktura `board_json`

JSON ma odzwierciedlac frontendowy model `BoardData`:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Task title",
      "details": "Task details"
    }
  }
}
```

Wymagane reguly walidacji (na etapie API, Czesc 6):
- `columns` i `cards` sa wymagane,
- `cardIds` w kolumnach musza wskazywac istniejace rekordy w `cards`,
- `id` karty i klucz w mapie `cards` musza byc zgodne,
- brak duplikatow `cardIds` pomiedzy kolumnami.

## Operacje danych (plan na Czesc 6)

- Odczyt tablicy:
  - znajdz `users.id` po `username`,
  - pobierz `kanban_boards.board_json` po `user_id`.
- Zapis tablicy:
  - waliduj payload JSON,
  - `UPDATE kanban_boards SET board_json=?, updated_at=?, version=version+1 WHERE user_id=?`.
- Inicjalizacja:
  - utworz rekord `users` dla `user`,
  - utworz domyslny `kanban_boards` z danymi startowymi, jesli brak.

## Dlaczego JSON w MVP

- Prostsza implementacja i szybszy time-to-value.
- Latwa zgodnosc z obecnym modelem frontendu.
- Mniej migracji na starcie projektu.
- Wada: slabiej query-owalne dane na poziomie SQL (akceptowalne w MVP).

## Ryzyka i granice

- Brak granularnych update SQL (zapis calego snapshotu).
- Potencjalne konflikty zapisu przy rownoleglych zmianach (na MVP akceptowalne).
- Brak historii zmian tablicy (mozna dodac pozniej jako osobna tabela audit/log).

## Kryteria akceptacji Czesc 5

- Schemat wspiera wielu uzytkownikow strukturalnie.
- W MVP wymusza jedna tablice per uzytkownik.
- Dane tablicy sa przechowywane jako JSON i walidowalne (`json_valid`).
- Podejscie jest zaakceptowane przed implementacja API danych (Czesc 6).
