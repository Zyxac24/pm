# Code Review — Kanban Board MVP

**Data przeglądu:** 2026-03-10
**Wersja:** commit `a5e27fd` (branch `main`)

---

## Podsumowanie

Projekt jest dobrze zorganizowanym MVP z czytelną architekturą. Główne ryzyka dotyczą bezpieczeństwa (brak autentykacji po stronie backendu) oraz braków w pokryciu testami modułów AI. Poniżej szczegółowa analiza.

| Kategoria | Krytyczne | Wysokie | Średnie | Niskie |
|-----------|:---------:|:-------:|:-------:|:------:|
| Bezpieczeństwo | 3 | 2 | 2 | 1 |
| Jakość kodu | — | 4 | 6 | 4 |
| Testy | — | 3 | 4 | 3 |
| Architektura | — | 2 | 3 | 2 |

---

## 1. Krytyczne problemy bezpieczeństwa

### 1.1 Klucz API w repozytorium
- **Plik:** `backend/.env`
- **Problem:** Klucz `OPENROUTER_API_KEY` przechowywany w repozytorium git (widoczny w historii commitów).
- **Wpływ:** Każdy z dostępem do repo może używać klucza.
- **Zalecenie:** Natychmiast unieważnić klucz. Dodać `.env` do `.gitignore`. Wyczyścić historię git (`git filter-branch` lub BFG Repo-Cleaner).

### 1.2 Brak autentykacji po stronie backendu
- **Pliki:** `backend/app/main.py` (wszystkie endpointy API)
- **Problem:** Backend nie weryfikuje tokenów ani danych uwierzytelniających. Każdy endpoint ufa nazwie użytkownika z URL.
- **Wpływ:** Dowolny użytkownik może uzyskać dostęp do tablicy innego użytkownika zmieniając `username` w URL.
- **Zalecenie:** Wdrożyć walidację JWT po stronie serwera (middleware FastAPI).

### 1.3 Hardcoded credentials we frontendzie
- **Plik:** `frontend/src/lib/auth.ts` (linie 4-5)
- **Problem:** Dane logowania (`user/password`) wpisane na stałe w kodzie źródłowym.
- **Uwaga:** Akceptowalne dla MVP/demo, ale musi być udokumentowane jako ograniczenie.

---

## 2. Problemy w backendzie (Python)

### 2.1 Hardcoded model AI
- **Plik:** `backend/app/ai_client.py`
- **Problem:** Model `openai/gpt-oss-120b` wpisany na stałe.
- **Zalecenie:** Przenieść do zmiennej środowiskowej `OPENROUTER_MODEL`.

### 2.2 Hardcoded CORS origins
- **Plik:** `backend/app/main.py`
- **Problem:** Lista dozwolonych origin-ów zawiera tylko adresy deweloperskie (`localhost:3000`, `localhost:8000`).
- **Zalecenie:** Konfiguracja przez zmienną środowiskową. W produkcji ograniczyć do domeny docelowej.

### 2.3 Bardzo krótki timeout bazy danych
- **Plik:** `backend/app/db.py`
- **Problem:** `timeout=2.0` (2 sekundy) — pod obciążeniem może powodować częste błędy.
- **Zalecenie:** Zwiększyć do 10-30 sekund lub uczynić konfigurowalnym.

### 2.4 Brak obsługi rollback w transakcjach
- **Plik:** `backend/app/db.py`
- **Problem:** `update_board()` nie obsługuje częściowych awarii — brak `try/except` wokół operacji DB.
- **Zalecenie:** Użyć context managera `with connection:` dla automatycznego rollback.

### 2.5 Ręcznie zbudowany JSON Schema dla AI
- **Plik:** `backend/app/ai_client.py` (linie ~47-102)
- **Problem:** Schema JSON do Structured Outputs konstruowana ręcznie — trudna w utrzymaniu, ryzyko rozbieżności z modelami Pydantic.
- **Zalecenie:** Generować schema z modeli Pydantic (`model.model_json_schema()`).

### 2.6 Ciche generowanie ID kart
- **Plik:** `backend/app/kanban_patch.py`
- **Problem:** Gdy AI nie poda `cardId`, generowany jest automatycznie — niedeterministyczne zachowanie.
- **Zalecenie:** Rozważyć czy brak ID powinien być błędem walidacji.

### 2.7 Brak pinowania wersji zależności
- **Plik:** `backend/pyproject.toml`
- **Problem:** Zależności używają `>=` zamiast przypiętych wersji — ryzyko niekompatybilnych aktualizacji.
- **Zalecenie:** Użyć `~=` lub dokładnych wersji. Rozważyć `uv lock`.

---

## 3. Problemy we frontendzie (TypeScript/React)

### 3.1 Brak walidacji runtime odpowiedzi API
- **Pliki:** `frontend/src/lib/kanbanApi.ts`, `frontend/src/lib/aiChatApi.ts`
- **Problem:** Odpowiedzi API rzutowane na typy TypeScript bez walidacji runtime (`as BoardData`).
- **Wpływ:** Zmiana struktury API spowoduje trudne do zdiagnozowania błędy.
- **Zalecenie:** Dodać walidację z biblioteką Zod.

### 3.2 Brak timeoutu dla requestów fetch
- **Plik:** `frontend/src/lib/kanbanApi.ts`
- **Problem:** Brak `AbortController` z timeoutem — jeśli backend zawiesi się, frontend czeka w nieskończoność.
- **Zalecenie:** Dodać `AbortController` z timeoutem 10-15 sekund.

### 3.3 Race condition przy edycji kart
- **Plik:** `frontend/src/components/KanbanCard.tsx` (linie ~20-23)
- **Problem:** `useEffect` synchronizuje draft z kartą — jeśli AI zmodyfikuje kartę podczas edycji, zmiany użytkownika zostaną nadpisane.
- **Scenariusz:** Użytkownik edytuje tytuł → AI przenosi kartę → draft jest resetowany.
- **Zalecenie:** Dodać flagę `isEditing` blokującą synchronizację zewnętrzną.

### 3.4 Brak limitu długości wiadomości AI
- **Plik:** `frontend/src/components/AiSidebarChat.tsx`
- **Problem:** Textarea nie ma `maxLength` — użytkownik może wkleić ogromny tekst.
- **Zalecenie:** Dodać `maxLength={2000}` i walidację po stronie backendu.

### 3.5 Brak możliwości anulowania żądań AI
- **Problem:** Gdy żądanie do AI trwa długo, użytkownik nie może go przerwać.
- **Zalecenie:** Dodać przycisk "Anuluj" z `AbortController`.

### 3.6 Brak paginacji historii czatu
- **Plik:** `frontend/src/components/AiSidebarChat.tsx`
- **Problem:** Wiadomości czatu renderowane bez wirtualizacji — rosną bez ograniczeń.
- **Zalecenie:** Dodać limit wyświetlanych wiadomości lub wirtualizację listy.

---

## 4. Luki w testach

### 4.1 Brak testów jednostkowych dla `ai_client.py`
- **Brakuje:** Testy `run_connectivity_test()`, `run_structured_kanban_chat()`, parsowanie odpowiedzi, edge case'y.

### 4.2 Brak testów jednostkowych dla `kanban_patch.py`
- **Brakuje:** Testy operacji `create_card`, `edit_card`, `move_card`, obsługa błędów, walidacja pozycji.

### 4.3 Brak testów rate limitingu
- **Brakuje:** Weryfikacja progów, reset limitu po oknie czasowym.

### 4.4 Niekompletne testy autentykacji (frontend)
- **Plik:** `frontend/src/lib/auth.test.ts`
- **Brakuje:** Testy localStorage, persystencja sesji, logout.

### 4.5 Brak testów E2E
- **Uwaga:** Konfiguracja Playwright istnieje, ale brak faktycznych testów E2E dla kluczowych flow (logowanie, drag-and-drop, czat AI).

---

## 5. Problemy architektoniczne

### 5.1 Brak obsługi współbieżnych edycji
- **Problem:** Przy jednoczesnej edycji z dwóch klientów — wygrywa ostatni zapis. Brak detekcji konfliktów ani wersjonowania.
- **Zalecenie:** Dodać pole `version` do tablicy i mechanizm optimistic locking.

### 5.2 Duplikacja modelu tablicy
- **Problem:** Struktura tablicy zdefiniowana niezależnie w TypeScript (`kanban.ts`) i Python (`models.py`). Zmiana wymaga modyfikacji w obu miejscach.
- **Zalecenie:** Generować typy TypeScript z OpenAPI schema FastAPI.

### 5.3 Rate limiting oparty wyłącznie na IP
- **Plik:** `backend/app/main.py`
- **Problem:** Za reverse proxy/load balancerem wszyscy użytkownicy mają to samo IP.
- **Zalecenie:** Uwzględnić nagłówki `X-Forwarded-For` lub kombinację IP + username.

---

## 6. Pozytywne aspekty

- **Czytelna struktura projektu** — wyraźny podział backend/frontend, logiczne nazewnictwo plików.
- **Dobre modele Pydantic** — walidatory, typy, strukturyzowane odpowiedzi AI.
- **SQLite z WAL mode** — pragmatyczny wybór dla MVP.
- **Dobrze zintegrowany drag-and-drop** — dnd-kit poprawnie użyty z hookami React.
- **Parametryzowane zapytania SQL** — brak podatności na SQL injection.
- **React escapuje domyślnie** — brak ryzyka XSS w standardowych komponentach.
- **Docker multi-stage build** — efektywny obraz produkcyjny.
- **TypeScript i Python typing** — stosowane konsekwentnie w całym projekcie.

---

## 7. Rekomendowane priorytety

### Natychmiast (Critical)
1. Unieważnić i zregenerować klucz OpenRouter API
2. Dodać `.env` do `.gitignore`, wyczyścić historię git
3. Wdrożyć walidację tokenów po stronie backendu

### Wysoki priorytet
4. Dodać timeouty do requestów fetch (frontend)
5. Naprawić race condition w edycji kart (`KanbanCard.tsx`)
6. Dodać testy dla `ai_client.py` i `kanban_patch.py`

### Średni priorytet
7. Przenieść konfigurację (CORS, model AI, timeout DB) do zmiennych środowiskowych
8. Dodać walidację runtime odpowiedzi API (Zod)
9. Dodać `maxLength` na textarea czatu AI
10. Wdrożyć testy E2E (Playwright)

### Niski priorytet
11. Paginacja/wirtualizacja historii czatu
12. Generowanie typów TS z OpenAPI schema
13. Optimistic locking dla współbieżnych edycji
