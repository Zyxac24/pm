# Raport przeglądu kodu — Kanban MVP

Data: 2026-03-09

---

## Podsumowanie

| Kategoria | Liczba |
|-----------|--------|
| Krytyczne | 6 |
| Ważne | 9 |
| Drobne | 13 |
| Razem | 28 |

---

## Problemy krytyczne

### K1. Brak middleware CORS

**Plik:** `backend/app/main.py`

FastAPI domyślnie nie ogranicza żadnych origin. Dowolna strona z zewnątrz może wysyłać żądania do `/api/kanban/` i `/api/ai/chat/`. Szczególnie niebezpieczne dla endpointu AI (OpenRouter generuje koszty).

```python
app = FastAPI(title="Kanban MVP Backend", lifespan=lifespan)
# Brak CORSMiddleware
```

**Rekomendacja:** Dodać `CORSMiddleware` z `allow_origins=["http://localhost:3000", "http://localhost:8000"]`.

---

### K2. Brak rate limitingu na endpointach AI

**Plik:** `backend/app/main.py`, linie 36 i 72

Endpoint `/api/ai/chat/{username}` i `/api/ai/test` nie mają żadnego ograniczenia liczby żądań. Każde zapytanie generuje realne koszty w OpenRouter.

**Scenariusz:** pętla curl z 1000 requestów wyśle 1000 płatnych promptów.

**Rekomendacja:** Dodać `slowapi` lub własny token-bucket na poziomie aplikacji.

---

### K3. Brak walidacji formatu `username` w URL

**Plik:** `backend/app/main.py`, linie 53, 72 i 124

Parametr `username` z URL jest przekazywany bezpośrednio do bazy bez żadnej walidacji formatu (długość, dozwolone znaki). Choć parameterized queries chronią przed SQL injection, brak filtrowania otwiera drogę np. do path traversal w przyszłych rozszerzeniach.

**Rekomendacja:** Dodać walidację Pydantic (regex `^[a-z0-9_-]{1,32}$`) w signatury endpointów.

---

### K4. Ryzyko nadpisania danych — brak optimistic locking

**Plik:** `backend/app/db.py`, linie 145–175

`update_board()` pobiera `user_id` a potem wykonuje UPDATE bez sprawdzania wersji. Jeśli dwa żądania nadejdą równocześnie (np. zapis frontendu + zapis z patcha AI), jedno z nich nadpisze drugie bez ostrzeżenia.

```python
UPDATE kanban_boards SET board_json = ?, version = version + 1
WHERE user_id = ?   -- brak: AND version = ?
```

**Rekomendacja:** Przekazywać oczekiwaną wersję i odrzucać zapis przy niezgodności.

---

### K5. Race condition — zapis po każdym drag-and-drop bez debounce

**Plik:** `frontend/src/components/KanbanBoard.tsx`, linie 59–67

Każde zakończenie przeciągania wywołuje `persistBoard()` (PUT do API). Szybkie przesunięcie kilku kart z rzędu wysyła wiele równoległych żądań. Odpowiedź z opóźnionym żądaniem może nadpisać nowszą wersję tablicy.

```typescript
const handleDragEnd = (event: DragEndEvent) => {
    applyBoardUpdate(...);  // od razu wywołuje persistBoard
};
```

**Rekomendacja:** Debounce `persistBoard` (np. 500 ms).

---

### K6. Brak limitu operacji w patchu AI

**Plik:** `backend/app/kanban_patch.py`, linia 18

Patch może zawierać dowolną liczbę operacji. Złośliwy lub błędny model mógłby wysłać dziesiątki tysięcy operacji i zawiesić serwer.

**Rekomendacja:**
```python
MAX_PATCH_OPERATIONS = 50
if len(patch.operations) > MAX_PATCH_OPERATIONS:
    raise AiPatchError("Patch exceeds maximum allowed operations.")
```

---

## Problemy ważne

### W1. `type assertion` zamiast runtime validation w API kliencie

**Plik:** `frontend/src/lib/kanbanApi.ts`, linie 22 i 39

```typescript
return (await response.json()) as BoardData;
```

`as BoardData` nie waliduje struktury w runtime. Jeśli backend zwróci inny kształt danych, TypeScript nie wykryje błędu, a komponent może otrzymać `undefined` w niespodziewanym miejscu.

**Rekomendacja:** Dodać walidację Zod lub ręczny guard sprawdzający kluczowe pola.

---

### W2. Niespójna obsługa błędów w endpoincie AI

**Plik:** `backend/app/main.py`, linie 72–115

Błędy OpenRouter zwracają 500/502, błędy patcha zwracają 422. Jeśli patch się nie powiedzie, AI już odpowiedziała i wiadomość trafiła do historii. Frontend nie ma mechanizmu cofnięcia komunikatu.

**Rekomendacja:** Rozważyć zwracanie odpowiedzi AI nawet przy błędzie patcha (z informacją dla użytkownika zamiast wyjątku HTTP).

---

### W3. Brak logowania zdarzeń na backendzie

Żaden plik backendu nie używa modułu `logging`. Brak informacji kto i kiedy zmienił tablicę, jakie błędy wystąpiły, czy patch AI się powiódł.

**Rekomendacja:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Board updated for user %s (version %d)", username, new_version)
```

---

### W4. Brak obsługi postępu podczas oczekiwania na AI

**Plik:** `frontend/src/components/AiSidebarChat.tsx`

Timeout OpenRouter wynosi 45 s (`ai_client.py` linia 172). Frontend nie pokazuje żadnego wskaźnika aktywności podczas oczekiwania. Użytkownik może myśleć, że aplikacja się zawiesiła.

**Rekomendacja:** Dodać spinner lub komunikat "AI is thinking..." widoczny podczas oczekiwania.

---

### W5. Magiczne string z ID kolumn rozsiane po 4 miejscach

ID kolumn (`col-backlog`, `col-todo`, itd.) są zduplikowane w:
- `backend/app/models.py` — `FIXED_COLUMN_IDS`
- `backend/app/db.py` — `DEFAULT_BOARD`
- `frontend/src/lib/kanban.ts` — `initialData`
- `backend/tests/test_main_api.py` — literały

Zmiana jednego ID wymaga aktualizacji we wszystkich czterech miejscach.

**Rekomendacja:** Wydzielić listę ID kolumn do jednego pliku konfiguracyjnego (backend: `config.py`, frontend: `kanban.ts` jako single source of truth).

---

### W6. Kolizje ID kart przy dużej liczbie kart

**Plik:** `frontend/src/lib/kanban.ts`, linie 164–168

```typescript
const randomPart = Math.random().toString(36).slice(2, 8);  // 6 znaków = ~46656 kombinacji
```

Przy kilkuset kartach prawdopodobieństwo kolizji rośnie. Brak mechanizmu wykrywania duplikatów ID.

**Rekomendacja:** Użyć `crypto.randomUUID()` (dostępne w Node i przeglądarkach).

---

### W7. Ciche ignorowanie błędów drag-and-drop

**Plik:** `frontend/src/lib/kanban.ts`, linia 91

```typescript
if (!activeColumnId || !overColumnId) {
    return columns;  // cichy fallback, brak logowania
}
```

Gdy przeciągany element nie istnieje w żadnej kolumnie, operacja jest odrzucana bez żadnej informacji. W trybie deweloperskim brak `console.warn` utrudnia debugowanie.

---

### W8. Brak PRAGMA `journal_mode = WAL` w SQLite

**Plik:** `backend/app/db.py`, linia 177

Domyślny tryb journal DELETE jest wolniejszy przy concurrent reads i bardziej podatny na korupcję przy przerwaniu procesu. Aplikacja serwuje request API + FastAPI lifespan jednocześnie.

**Rekomendacja:** Dodać `connection.execute("PRAGMA journal_mode = WAL;")` obok istniejącego `PRAGMA foreign_keys = ON`.

---

### W9. Brak testu E2E dla czatu AI

**Plik:** `frontend/tests/kanban.spec.ts`

Testy Playwright nie pokrywają przepływu AI chat. Jest to kluczowa funkcjonalność Części 10, a brak E2E oznacza, że integracja frontend–backend–OpenRouter nie jest weryfikowana w automatycznym teście.

---

## Problemy drobne

### D1. Brak Error Boundary w drzewie komponentów

`KanbanBoard.tsx` nie opakowuje `DndContext` w React Error Boundary. Wyjątek w obsłudze dnd-kit lub komponencie karty spowoduje biały ekran bez komunikatu.

---

### D2. Fallback strona (`static/index.html`) nie istnieje

**Plik:** `backend/app/main.py`, linia 25

`FALLBACK_INDEX_PATH` wskazuje na `app/static/index.html`, który nie jest obecny w repozytorium. Jeśli folder `frontend_dist/` nie istnieje (np. lokalna praca bez buildu), backend zwróci 500 zamiast czytelnego komunikatu.

---

### D3. Błąd catch w `loadBoard` nie loguje szczegółów

**Plik:** `frontend/src/components/KanbanBoard.tsx`, linia 39

```typescript
} catch {  // brak parametru error
    setLoadError("Could not load board from backend. Showing local snapshot.");
}
```

Brak `console.error(error)` utrudnia diagnostykę problemów sieciowych.

---

### D4. Timeout bazy danych nie jest ustawiony

**Plik:** `backend/app/db.py`, linia 177

`sqlite3.connect(self.db_path)` używa domyślnego timeoutu 5 s. W środowisku z wysokim I/O lub zablokowanym plikiem BD serwer może zawiesić wątek na 5 sekund bez informacji zwrotnej.

**Rekomendacja:** `sqlite3.connect(self.db_path, timeout=2.0)`.

---

### D5. Niespójne typy wyjątków w logice biznesowej

Warstwa biznesowa rzuca `ValueError` (models.py), `OpenRouterConfigError`, `AiPatchError` — brak wspólnej hierarchii. Utrudnia centralne łapanie błędów.

---

### D6. Brak testu dla nieznanej operacji patcha przez model AI

**Plik:** `backend/tests/test_main_api.py`

Pydantic odrzuca nieznaną wartość `op` dzięki `Literal[...]` — to poprawne zachowanie — ale brak testu potwierdzającego, że odpowiedź backendowi z nieznaną operacją daje czytelny błąd 422 (nie 500).

---

### D7. Brak testu dla concurrent updates (race condition)

**Plik:** `backend/tests/test_db_repository.py`

Brak testu sprawdzającego scenariusz: dwa równoległe `update_board()` — które dane wygrywają i czy nie dochodzi do uszkodzenia danych.

---

### D8. `void` przy `persistBoard` ukrywa odrzucone Promise

**Plik:** `frontend/src/components/KanbanBoard.tsx`, linia 65

```typescript
void persistBoard(next);
```

`void` celowo ignoruje Promise. Jeśli `persistBoard` rzuci, błąd jest połykany bez informacji dla użytkownika (poza `setSyncError` w samej funkcji — tu OK, ale wymaga uważnego śledzenia).

---

### D9. Brak `aria-label` na przyciskach akcji kart

**Plik:** `frontend/src/components/KanbanCard.tsx`

Przyciski edycji i usuwania kart nie mają atrybutów `aria-label`. Aplikacja jest niedostępna dla czytników ekranu.

---

### D10. Hardcoded `DEMO_USERNAME = "user"` w wielu plikach frontendu

Stała pojawia się w `auth.ts`, `KanbanBoard.tsx` i testach. Przy zmianie nazwy użytkownika demo wymagane są zmiany w kilku miejscach.

---

### D11. Brak informacji o wersji API w `/api/health`

Odpowiedź `{"status":"ok","service":"backend"}` nie zawiera wersji aplikacji. Utrudnia diagnozowanie problemów w środowiskach z wieloma instancjami.

---

### D12. `pyproject.toml` nie deklaruje zależności deweloperskich

`pytest` i `pytest-cov` nie są wymienione w `pyproject.toml`. Instalacja środowiska testowego wymaga ręcznych kroków spoza dokumentacji.

**Rekomendacja:**
```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]
```

---

### D13. Brak `.dockerignore`

Brak pliku `.dockerignore` może powodować kopiowanie `node_modules/`, `.venv/`, plików `.env` i katalogów testowych do warstw obrazu Dockera, co zwiększa jego rozmiar i czas budowania.

---

## Top 5 zaleceń priorytetowych

1. **Dodać CORSMiddleware** z ograniczeniem do znanych origin — ochrona przed nieautoryzowanymi żądaniami zewnętrznymi.
2. **Wdrożyć rate limiting na endpointach AI** — ochrona kosztów OpenRouter przed nadużyciem.
3. **Dodać debounce dla `persistBoard`** — eliminacja race condition przy szybkim drag-and-drop.
4. **Dodać limit operacji w patchu AI** — ochrona przed DoS przez nadmierną liczbę operacji.
5. **Dodać `pytest` do `[project.optional-dependencies]`** — umożliwia odtworzenie środowiska testowego jednym poleceniem.
