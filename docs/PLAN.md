# Główne etapy projektu

Część 1: Planowanie

Rozbuduj ten dokument, planując szczegółowo każdy z etapów, z podpunktami ujętymi jako lista kontrolna do odznaczania przez agenta, wraz z testami i kryteriami sukcesu dla każdego z nich. Utwórz także plik AGENTS.md w katalogu frontend, opisujący istniejący tam kod. Upewnij się, że użytkownik sprawdzi i zaakceptuje plan.

Część 2: Szkielet projektu

Skonfiguruj infrastrukturę Dockera, backend w katalogu backend/ za pomocą FastAPI oraz napisz skrypty uruchamiania i zatrzymywania w katalogu scripts/. Powinno to serwować przykładowy statyczny HTML, aby potwierdzić działanie przykładu "hello world" uruchamianego lokalnie oraz umożliwić wykonanie zapytania do API.

Część 3: Dodanie frontendu

Zaktualizuj projekt tak, aby frontend był statycznie budowany i serwowany, tak aby aplikacja wyświetlała demo tablicy Kanban na ścieżce /. Pełne testy jednostkowe oraz integracyjne.

Część 4: Dodanie fikcyjnego logowania użytkownika

Zaktualizuj aplikację tak, aby po wejściu na / wymagane było zalogowanie przy użyciu przykładowych danych ("user", "password"), by zobaczyć tablicę Kanban, oraz możliwość wylogowania. Pełne testy.

Część 5: Modelowanie bazy danych

Zaproponuj schemat bazy danych dla Kanbana, zapisując dane jako JSON. Udokumentuj podejście do bazy w katalogu docs/ i uzyskaj akceptację użytkownika.

Część 6: Backend

Dodaj trasy API pozwalające backendowi odczytać oraz modyfikować tablicę Kanban dla danego użytkownika; dokładnie przetestuj za pomocą testów jednostkowych backendu. Baza danych powinna być tworzona, jeśli nie istnieje.

Część 7: Frontend + Backend

Połącz frontend z backendem tak, aby aplikacja stanowiła trwałą tablicę Kanban. Przeprowadź bardzo dokładne testy.

Część 8: Połączenie z AI

Pozwól backendowi wykonywać zapytania do AI przez OpenRouter. Przetestuj połączenie prostym testem "2+2" i upewnij się, że połączenie działa.

Część 9: Rozszerzenie połączenia z AI w backendzie, tak by zawsze przekazywać do AI JSON tablicy Kanban, pytanie użytkownika (oraz historię rozmowy). AI powinno odpowiadać w formie Structured Outputs, zawierającej odpowiedź dla użytkownika oraz opcjonalnie aktualizację tablicy Kanban. Dokładnie przetestuj.

Część 10: Dodaj nowoczesny panel boczny do interfejsu wspierający pełny czat z AI, umożliwiając LLM, w zależności od potrzeby, aktualizację Kanbana na podstawie odpowiedzi w Structured Outputs. Jeśli AI zaktualizuje Kanban, UI powinno automatycznie się odświeżyć.