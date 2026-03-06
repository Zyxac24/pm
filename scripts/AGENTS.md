# Scripts: start/stop Docker (Czesc 2)

W tym katalogu znajduja sie skrypty do uruchamiania i zatrzymywania aplikacji:

- Linux: `start-linux.sh`, `stop-linux.sh`
- Mac: `start-mac.sh`, `stop-mac.sh`
- Windows: `start-windows.bat`, `stop-windows.bat`

Kazdy skrypt:
- przechodzi do katalogu glownego projektu,
- uruchamia `docker compose` z odpowiednia komenda,
- pozostaje prosty i bez dodatkowej logiki.