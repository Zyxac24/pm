# MVP aplikacji do zarządzania projektami

## Wymagania biznesowe

Ten projekt polega na stworzeniu aplikacji do zarządzania projektami. Kluczowe funkcje:
- Użytkownik może się zalogować
- Po zalogowaniu użytkownik widzi tablicę Kanban reprezentującą jego projekt
- Tablica Kanban ma stałe kolumny, które można przemianować
- Karty na tablicy Kanban można przenosić metodą przeciągnij i upuść oraz edytować
- W pasku bocznym dostępny jest czat AI; AI potrafi tworzyć, edytować oraz przenosić jedną lub więcej kart

## Ograniczenia

W MVP będzie tylko jedno logowanie użytkownika (na stałe: ‘user’ i ‘password’), ale baza danych będzie wspierać wielu użytkowników w przyszłości.

W MVP dozwolona będzie tylko jedna tablica Kanban na zalogowanego użytkownika.

W MVP wszystko będzie działać lokalnie (w kontenerze Dockera)

## Decyzje techniczne

- Frontend NextJS
- Backend Python FastAPI, wraz z obsługą statycznej strony NextJS na /
- Wszystko spakowane w jeden kontener Dockera
- Jako menedżer pakietów Pythona w kontenerze używamy "uv"
- Do wywołań AI wykorzystujemy OpenRouter. Klucz OPENROUTER_API_KEY znajduje się w pliku .env w katalogu głównym projektu
- Używamy modelu `openai/gpt-oss-120b`
- Lokalna baza danych SQLLite; baza tworzona, jeśli nie istnieje
- Skrypty uruchamiania i zatrzymywania serwera dla Mac, PC, Linux w scripts/

## Punkt startowy

Działający MVP frontendu jest już dostępny w katalogu frontend. Nie jest jeszcze przystosowany do pracy w Dockerze. To czysta demonstracja frontendu.

## Schemat kolorów

- Żółty akcent: `#ecad0a` — linie akcentujące, wyróżnienia
- Niebieski główny: `#209dd7` — linki, kluczowe sekcje
- Fioletowy wtórny: `#753991` — przyciski przesyłania, ważne akcje
- Ciemny granat: `#032147` — główne nagłówki
- Szary tekst: `#888888` — tekst pomocniczy, etykiety

## Standardy kodowania

1. Używaj najnowszych wersji bibliotek i zgodnych ze współczesnymi standardów.
2. Zachowuj prostotę — NIGDY nie przekombinuj, ZAWSZE upraszczaj, NIE stosuj zbędnej defensywności. Bez dodatkowych funkcji — skup się na prostocie.
3. Bądź zwięzły. README ma być minimalistyczny. WAŻNE: żadnych emoji.
4. W przypadku problemów zawsze identyfikuj przyczynę przed próbą naprawy. Nie zgaduj. Najpierw znajdź dowód, potem napraw przyczynę.

## Dokumentacja robocza

Wszystkie dokumenty do planowania i realizacji projektu będą w katalogu docs/.
Proszę zapoznać się z dokumentem docs/PLAN.md przed rozpoczęciem pracy.