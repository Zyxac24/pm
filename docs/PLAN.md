# Plan realizacji MVP

## Zasady wykonania

- [ ] Praca etapami od Części 1 do Części 10.
- [ ] Start kolejnej części tylko po uprzedniej akceptacji użytkownika.
- [ ] W każdym etapie wykonujemy realistyczne minimum testów (bez nadmiernej rozbudowy).
- [ ] W przypadku problemu najpierw znajdujemy przyczynę i dowód, dopiero potem naprawa.
- [ ] Dążymy do 80% pokrycia testami dla rozwijanego kodu, ale nie traktujemy tego jako twardego blokera.
- [ ] Priorytet: testy wartościowe dla ryzyk i kluczowych scenariuszy, nie sztuczne testy "pod licznik".
- [ ] Jeśli 80% nie zostanie osiągnięte, dokumentujemy brakujące obszary i uzasadnienie.

## Strategia testów i pokrycia

- [ ] Każdy etap zawiera minimum: testy jednostkowe logiki krytycznej + co najmniej jeden test integracyjny/E2E dla głównego przepływu.
- [ ] Pokrycie mierzymy regularnie podczas etapów implementacyjnych (frontend/backend) i raportujemy wynik po etapie.
- [ ] Dodatkowe testy dopisujemy tam, gdzie zmniejszają ryzyko regresji lub chronią ważny kontrakt API/UI.
- [ ] Nie dodajemy testów niskiej wartości tylko po to, by sztucznie podbić pokrycie.

## Status i decyzje wykonawcze (Części 1-10)

### Status etapów

- [x] Część 1 zakończona i zaakceptowana.
- [x] Część 2 zakończona i zaakceptowana.
- [x] Część 3 zakończona i zaakceptowana.
- [x] Część 4 zakończona i zaakceptowana.
- [x] Część 5 zakończona i zaakceptowana.
- [x] Część 6 zakończona i zaakceptowana.
- [x] Część 7 zakończona i zaakceptowana.
- [x] Część 8 zakończona i zaakceptowana.
- [x] Część 9 zakończona i zaakceptowana.
- [ ] Część 10 wykonana technicznie, oczekuje na akceptację użytkownika.

### Decyzje zrealizowane

- [x] Część 4: logowanie jest frontendowe, token przechowywany po stronie frontendu (`localStorage`).
- [x] Część 5: model danych oparty o `users` + `kanban_boards` z JSON snapshot (`docs/DATABASE_SCHEMA.md`).
- [x] Część 6: backend udostępnia `GET` i `PUT` pod `/api/kanban/{username}`.
- [x] Część 6: baza SQLite tworzy się automatycznie przy starcie, wraz z seedem użytkownika `user`.
- [x] Część 6: payload tablicy ma walidację spójności (integralność kart i kolumn).
- [x] Część 7: frontend pobiera i zapisuje tablicę przez API backendu (zamiast lokalnego stanu demo).
- [x] Część 7: trwałość danych między restartami zapewnia Docker volume (`kanban_data`).
- [x] Część 7: dodana minimalna obsługa błędów sieciowych w UI (load/sync + retry).
- [x] Część 8: backend zintegrowany z OpenRouter przez `OPENROUTER_API_KEY` i model `openai/gpt-oss-120b`.
- [x] Część 8: dodany endpoint techniczny `POST /api/ai/test` wykonujący test promptem `2+2`.
- [x] Część 8: brak klucza środowiskowego zwraca kontrolowany, czytelny błąd.
- [x] Część 9: prompt backendu rozszerzony o JSON tablicy, historię i pytanie użytkownika.
- [x] Część 9: odpowiedź AI wymuszona przez Structured Outputs i walidowana po stronie backendu.
- [x] Część 9: dodany format odpowiedzi `message + optional patch` oraz bezpieczne zastosowanie patcha.
- [x] Część 10: dodany panel boczny czatu AI w UI z historią rozmowy i wysyłką zapytań.
- [x] Część 10: po odpowiedzi backendu tablica odświeża się automatycznie danymi z odpowiedzi AI.

### Raport pokrycia i decyzje jakościowe

- [x] Część 4: pokrycie frontendu (`src/**`) ~63.86% lines; brak 80% zaakceptowany, bo testy skupione na kluczowych ścieżkach logowania i regresji.
- [x] Część 6: pokrycie backendu (`app/*`) ~54% globalnie; `db.py` i `models.py` ~96%, niski wynik globalny przez brak pełnego pokrycia `main.py` w pierwszym przebiegu.
- [x] Część 7: dołożono testy API i integracyjne, by podnieść pokrycie obszarów o najwyższym ryzyku regresji.
- [x] Część 8: dodano testy endpointu AI (ścieżka sukcesu, brak klucza, mapowanie błędu upstream) oraz test integracyjny z realnym OpenRouterem aktywny przy ustawionym kluczu.
- [x] Część 9: dodano testy odpowiedzi bez patcha, z patchem (create/edit/move) oraz test błędu odpowiedzi niezgodnej ze schematem.
- [x] Część 10: dodano testy UI czatu, aktualizacji widoku po patchu AI i utrzymano testy regresji operacji Kanban.

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
- [ ] Dokument referencyjny schematu: `docs/DATABASE_SCHEMA.md`.

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

- [x] Dodać integrację backendu z OpenRouter przez `OPENROUTER_API_KEY`.
- [x] Ustawić model `openai/gpt-oss-120b`.
- [x] Dodać prosty endpoint/test techniczny połączenia.

### Testy (realistyczne minimum)

- [x] Test połączenia AI z promptem `2+2`.
- [x] Obsługa braku klucza środowiskowego (czytelny błąd).

### Kryteria sukcesu

- [x] Backend poprawnie komunikuje się z OpenRouter.
- [x] Mamy potwierdzony działający przepływ request/response.

## Część 9: Structured Outputs dla AI + patch Kanbana

### Zakres

- [x] Rozszerzyć prompt backendu: JSON tablicy, pytanie użytkownika, historia rozmowy.
- [x] Wymusić odpowiedź AI w Structured Outputs.
- [x] Zdefiniować format odpowiedzi: wiadomość dla użytkownika + opcjonalny patch Kanbana.
- [x] Wdrożyć walidację i bezpieczne zastosowanie patcha po stronie backendu.

### Testy (realistyczne minimum)

- [x] Test poprawnej odpowiedzi bez patcha.
- [x] Test poprawnej odpowiedzi z patchem (create/edit/move).
- [x] Test odpowiedzi niezgodnej ze schematem (walidacja i błąd kontrolowany).

### Kryteria sukcesu

- [x] Backend przyjmuje i stosuje poprawny patch.
- [x] Błędny format odpowiedzi AI nie psuje danych tablicy.

## Część 10: Panel boczny czatu AI w UI

### Zakres

- [x] Dodać panel boczny czatu w interfejsie frontendu.
- [x] Obsłużyć historię rozmowy i wysyłkę zapytań do backendu.
- [x] Po odpowiedzi z patchem odświeżać tablicę automatycznie.
- [x] Zachować prosty, czytelny UX zgodny z kolorystyką projektu.

### Testy (realistyczne minimum)

- [x] Test UI: wysłanie wiadomości i wyświetlenie odpowiedzi AI.
- [x] Test integracyjny: odpowiedź AI z patchem aktualizuje widok tablicy.
- [x] Test regresji: podstawowe operacje Kanbana nadal działają.

### Kryteria sukcesu

- [x] Użytkownik może prowadzić czat AI w panelu bocznym.
- [x] Aktualizacje Kanbana z patcha AI są widoczne automatycznie.

## Reguła przejścia między etapami

- [ ] Po zakończeniu każdej części agent publikuje wynik i czeka na akceptację użytkownika.
- [ ] Bez akceptacji użytkownika nie rozpoczynamy kolejnej części.