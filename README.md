# Projekt WA - Monorepo Struktur

Dieses Repository ist als Monorepo fuer mehrere Django-Module aufgebaut, damit Updates mit einem zentralen Ablauf moeglich sind.

## Zielstruktur

- `jonasrsh.github.io/`: Modul 1 (Portfolio Website)
- `wa_automater/`: Modul 2 (WA Generator)
- `docker-compose.yml`: zentrale Orchestrierung
- `update.sh`: zentraler Build-/Migrations-/Static-Update-Flow
- `.env`: gemeinsame Konfiguration fuer beide Module
- `nginx.example.conf`, `nginx_website.conf`, `nginx_wa_generator.conf`: Reverse-Proxy-Konfiguration

Installations- und Update-Hinweise stehen in der separaten Datei `INSTALLATION.md`.