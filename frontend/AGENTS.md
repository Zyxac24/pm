# Frontend: opis aktualnego kodu (MVP demo)

## Cel

Frontend jest samodzielnym demo tablicy Kanban. Pokazuje:
- ekran logowania dla `/` z danymi demo (`user` / `password`),
- staly uklad 5 kolumn,
- edycje nazw kolumn,
- dodawanie i usuwanie kart,
- przenoszenie kart drag-and-drop.

Na tym etapie frontend nie ma backendowej autoryzacji ani trwalego zapisu danych.

## Stack i narzedzia

- Next.js (App Router), React, TypeScript
- Tailwind CSS 4
- dnd-kit (`@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`)
- Testy jednostkowe: Vitest + Testing Library
- Testy E2E: Playwright

## Wejscie aplikacji

- `src/app/page.tsx` renderuje `KanbanBoard`.
- `src/app/layout.tsx` ustawia globalny layout i fonty.
- `src/app/globals.css` zawiera kolory i style globalne (zgodne z paleta projektu).

## Glowna logika

### `src/components/KanbanBoard.tsx`

Komponent-klient zarzadzajacy stanem tablicy:
- trzyma lokalny stan `board` (`columns` + `cards`),
- obsluguje drag-and-drop (start/koniec),
- obsluguje zmiane nazwy kolumny,
- obsluguje dodanie i usuniecie karty,
- renderuje `KanbanColumn` dla kazdej kolumny,
- renderuje `DragOverlay` z `KanbanCardPreview`.

### `src/components/AuthGate.tsx`

Komponent-klient odpowiedzialny za dostep:
- sprawdza token w `localStorage`,
- pokazuje formularz logowania dla nieautoryzowanego uzytkownika,
- po poprawnych danych (`user` / `password`) zapisuje token i pokazuje tablice,
- obsluguje wylogowanie (usuniecie tokenu).

### `src/lib/kanban.ts`

Definicje modelu i logika pomocnicza:
- typy `Card`, `Column`, `BoardData`,
- `initialData` z 5 kolumnami i przykladowymi kartami,
- `moveCard(...)` do re-order i move miedzy kolumnami,
- `createId(...)` do generowania id nowych kart.

### `src/lib/auth.ts`

Definicje logowania demo:
- stale z loginem i haslem,
- klucz i wartosc tokenu frontendowego,
- `validateCredentials(...)` do walidacji danych logowania.

## Komponenty UI

- `src/components/KanbanColumn.tsx`:
  - strefa drop dla kolumny,
  - input do zmiany nazwy kolumny,
  - lista kart (`SortableContext`),
  - formularz dodawania karty.
- `src/components/KanbanCard.tsx`:
  - karta sortowalna (drag),
  - tytul + szczegoly,
  - przycisk usuwania.
- `src/components/NewCardForm.tsx`:
  - formularz otwierany przyciskiem,
  - walidacja: tytul wymagany.
- `src/components/KanbanCardPreview.tsx`:
  - podglad karty podczas przeciagania.

## Testy i konfiguracja testowa

- `src/lib/kanban.test.ts`: testy funkcji `moveCard`.
- `src/lib/auth.test.ts`: testy walidacji danych logowania.
- `src/components/KanbanBoard.test.tsx`: render kolumn, zmiana nazwy, dodanie/usuniecie karty.
- `tests/kanban.spec.ts`: logowanie, wylogowanie, smoke tablicy, operacje kart.
- `vitest.config.ts`: jsdom, setup testow, alias `@`.
- `playwright.config.ts`: uruchamia lokalny serwer Next.js podczas testow.

## Komendy (frontend/)

- `npm run dev` - lokalny dev server
- `npm run build` - build produkcyjny
- `npm run start` - start po buildzie
- `npm run test:unit` - testy jednostkowe
- `npm run test:e2e` - testy E2E
- `npm run test:all` - jednostkowe + E2E

## Stan obecny i ograniczenia

- Dane tablicy sa tylko w pamieci (reset po odswiezeniu).
- Logowanie jest tylko frontendowe (token w `localStorage`), bez bezpieczenstwa produkcyjnego.
- Brak integracji z backend API.
- Brak panelu czatu AI.

## Wskazowki dla kolejnych etapow

- Nie rozbudowywac frontendu ponad wymagania etapu.
- Najpierw integracja z backendem i logowaniem, potem AI.
- Utrzymac prosty model danych (`columns` + `cards`) i mapowanie patchy.
- Przy zmianach UI pilnowac aktualnej kolorystyki z `globals.css`.
