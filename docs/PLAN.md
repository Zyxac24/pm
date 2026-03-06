# Plan realizacji MVP

## Zasady wykonania

- [ ] Praca etapami od Części 1 do Części 10.
- [ ] Start kolejnej części tylko po uprzedniej akceptacji użytkownika.
- [ ] W każdym etapie wykonujemy realistyczne minimum testów (bez nadmiernej rozbudowy).
- [ ] W przypadku problemu najpierw znajdujemy przyczynę i dowód, dopiero potem naprawa.

## Część 1: Planowanie

### Zakres

- [ ] Rozbudować `docs/PLAN.md` do postaci checklisty z testami i kryteriami sukcesu.
- [ ] Utworzyć `frontend/AGENTS.md` opisujący istniejący kod frontendu.
- [ ] Zebrać pytania/ryzyka i uzyskać akceptację użytkownika przed Częścią 2.

### Testy (realistyczne minimum)

- [ ] Sprawdzenie ręczne, że oba dokumenty istnieją i są czytelne.
- [ ] Sprawdzenie ręczne, że plan zawiera wszystkie 10 części.
- [ ] Sprawdzenie ręczne, że każda część ma: zakres, testy, kryteria sukcesu.

### Kryteria sukcesu

- [ ] Użytkownik akceptuje plan i opis frontendu.
- [ ] Dokumentacja wystarcza, by rozpocząć Część 2 bez zgadywania założeń.

## Część 2: Szkielet projektu

### Zakres

- [ ] Przygotować `backend/` z aplikacją FastAPI i podstawową strukturą modułów.
- [ ] Dodać Dockerfile oraz konfigurację uruchamiania całego projektu w jednym kontenerze.
- [ ] Dodać skrypty `scripts/` dla Linux/Mac/Windows do startu i stopu.
- [ ] Serwować z backendu stronę testową "hello world" i prostą trasę API (np. `/api/health`).

### Testy (realistyczne minimum)

- [ ] Build obrazu Dockera przechodzi bez błędów.
- [ ] Kontener startuje lokalnie przez skrypt i odpowiada na `/api/health`.
- [ ] Wejście na `/` zwraca stronę testową.

### Kryteria sukcesu

- [ ] Jednym poleceniem uruchamiamy działającą aplikację w Dockerze.
- [ ] Backend i statyczna strona działają w jednym kontenerze.

## Część 3: Dodanie frontendu

### Zakres

- [ ] Zintegrować frontend Next.js z backendem tak, aby był budowany statycznie.
- [ ] Serwować demo tablicy Kanban na ścieżce `/`.
- [ ] Ustalić minimalny workflow build/run w Dockerze.

### Testy (realistyczne minimum)

- [ ] `frontend` build przechodzi.
- [ ] Demo Kanbana wyświetla się na `/`.
- [ ] Uruchomienie testów jednostkowych frontendu.
- [ ] Uruchomienie co najmniej kluczowego testu E2E (smoke).

### Kryteria sukcesu

- [ ] Użytkownik widzi działające demo Kanban po starcie kontenera.
- [ ] Bazowe testy frontendu przechodzą.

## Część 4: Fikcyjne logowanie użytkownika

### Zakres

- [ ] Dodać ekran logowania z danymi `user` / `password`.
- [ ] Zabezpieczyć dostęp do `/` tak, by bez logowania użytkownik widział formularz logowania.
- [ ] Przechowywać token po stronie frontendu (zgodnie z ustaleniem).
- [ ] Dodać wylogowanie (usunięcie tokenu i powrót do logowania).

### Testy (realistyczne minimum)

- [ ] Test jednostkowy/logiczny walidacji logowania.
- [ ] Test E2E: poprawne logowanie i dostęp do Kanbana.
- [ ] Test E2E: wylogowanie blokuje dostęp do tablicy.

### Kryteria sukcesu

- [ ] Bez tokenu użytkownik nie widzi tablicy.
- [ ] Po poprawnym logowaniu użytkownik widzi tablicę.
- [ ] Wylogowanie działa i czyści sesję frontendową.

## Część 5: Modelowanie bazy danych

### Zakres

- [ ] Zaprojektować schemat SQLite pod wielu użytkowników (z perspektywą rozwoju).
- [ ] Dla MVP utrzymać jedną tablicę Kanban na użytkownika.
- [ ] Przechowywać dane tablicy w JSON.
- [ ] Udokumentować schemat i decyzje w `docs/`.
- [ ] Uzyskać akceptację użytkownika przed implementacją API danych.

### Testy (realistyczne minimum)

- [ ] Sprawdzenie ręczne poprawności dokumentacji schematu.
- [ ] Prosty test tworzenia bazy, jeśli nie istnieje.

### Kryteria sukcesu

- [ ] Użytkownik akceptuje schemat.
- [ ] Schemat wspiera przyszłą wieloużytkownikowość bez zmiany podstaw modelu.

## Część 6: Backend API Kanban

### Zakres

- [ ] Dodać endpoint(y) odczytu tablicy Kanban dla użytkownika.
- [ ] Dodać endpoint(y) modyfikacji tablicy Kanban.
- [ ] Automatycznie tworzyć bazę przy starcie, jeśli nie istnieje.
- [ ] Zapewnić spójny kontrakt JSON dla frontendu.

### Testy (realistyczne minimum)

- [ ] Testy jednostkowe backendu dla operacji odczytu i zapisu.
- [ ] Testy ścieżek błędnych (np. brak użytkownika, niepoprawny payload).
- [ ] Test inicjalizacji bazy przy pustym środowisku.

### Kryteria sukcesu

- [ ] API zwraca i zapisuje dane tablicy poprawnie.
- [ ] Backend przechodzi testy minimalnego zakresu.

## Część 7: Integracja Frontend + Backend

### Zakres

- [ ] Podłączyć frontend do API backendu zamiast lokalnego stanu demo.
- [ ] Zapewnić trwałość danych tablicy między restartami aplikacji.
- [ ] Dodać minimalną obsługę błędów sieciowych w UI.

### Testy (realistyczne minimum)

- [ ] Test integracyjny: odczyt tablicy po zalogowaniu.
- [ ] Test integracyjny: zmiana tablicy i odświeżenie strony zachowuje dane.
- [ ] Test ręczny: scenariusz restartu kontenera i weryfikacja trwałości.

### Kryteria sukcesu

- [ ] Kanban działa na danych z backendu i zapisuje zmiany trwale.
- [ ] Kluczowe ścieżki użytkownika działają end-to-end.

## Część 8: Połączenie backendu z AI (OpenRouter)

### Zakres

- [ ] Dodać integrację backendu z OpenRouter przez `OPENROUTER_API_KEY`.
- [ ] Ustawić model `openai/gpt-oss-120b`.
- [ ] Dodać prosty endpoint/test techniczny połączenia.

### Testy (realistyczne minimum)

- [ ] Test połączenia AI z promptem `2+2`.
- [ ] Obsługa braku klucza środowiskowego (czytelny błąd).

### Kryteria sukcesu

- [ ] Backend poprawnie komunikuje się z OpenRouter.
- [ ] Mamy potwierdzony działający przepływ request/response.

## Część 9: Structured Outputs dla AI + patch Kanbana

### Zakres

- [ ] Rozszerzyć prompt backendu: JSON tablicy, pytanie użytkownika, historia rozmowy.
- [ ] Wymusić odpowiedź AI w Structured Outputs.
- [ ] Zdefiniować format odpowiedzi: wiadomość dla użytkownika + opcjonalny patch Kanbana.
- [ ] Wdrożyć walidację i bezpieczne zastosowanie patcha po stronie backendu.

### Testy (realistyczne minimum)

- [ ] Test poprawnej odpowiedzi bez patcha.
- [ ] Test poprawnej odpowiedzi z patchem (create/edit/move).
- [ ] Test odpowiedzi niezgodnej ze schematem (walidacja i błąd kontrolowany).

### Kryteria sukcesu

- [ ] Backend przyjmuje i stosuje poprawny patch.
- [ ] Błędny format odpowiedzi AI nie psuje danych tablicy.

## Część 10: Panel boczny czatu AI w UI

### Zakres

- [ ] Dodać panel boczny czatu w interfejsie frontendu.
- [ ] Obsłużyć historię rozmowy i wysyłkę zapytań do backendu.
- [ ] Po odpowiedzi z patchem odświeżać tablicę automatycznie.
- [ ] Zachować prosty, czytelny UX zgodny z kolorystyką projektu.

### Testy (realistyczne minimum)

- [ ] Test UI: wysłanie wiadomości i wyświetlenie odpowiedzi AI.
- [ ] Test integracyjny: odpowiedź AI z patchem aktualizuje widok tablicy.
- [ ] Test regresji: podstawowe operacje Kanbana nadal działają.

### Kryteria sukcesu

- [ ] Użytkownik może prowadzić czat AI w panelu bocznym.
- [ ] Aktualizacje Kanbana z patcha AI są widoczne automatycznie.

## Reguła przejścia między etapami

- [ ] Po zakończeniu każdej części agent publikuje wynik i czeka na akceptację użytkownika.
- [ ] Bez akceptacji użytkownika nie rozpoczynamy kolejnej części.