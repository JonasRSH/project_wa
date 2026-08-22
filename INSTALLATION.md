# Installation und Updates

## Voraussetzungen

- Docker mit Docker Compose
- Zugriff auf dieses Repository

## Ersteinrichtung

1. Umgebungsdatei anlegen:

```bash
cp .env.example .env
```

2. Werte in `.env` setzen (Secrets, Hosts, Mail).

3. Optional: lokale, nicht versionierte Overrides anlegen:

```bash
cp docker-compose.local.example.yml docker-compose.local.yml
```

Alle host-spezifischen Anpassungen nur in `docker-compose.local.yml` pflegen.

## Update ausfuehren

```bash
./update.sh
```

Das Script fuehrt aus:

- `docker compose up -d --build` (inkl. lokalem Override, falls vorhanden)
- Migrationen fuer `website` und `wa-generator`
- `collectstatic` fuer beide Module
- Statusausgabe mit `docker compose ps`

## Standardablauf fuer kuenftige Deployments

1. `git pull --ff-only`
2. `./update.sh`

## Wichtige Regel fuer sensible Daten

- Basisdateien versioniert lassen: `docker-compose.yml`, `nginx.example.conf`, `nginx_website.conf`, `nginx_wa_generator.conf`
- Sensitive oder server-spezifische Daten nur in `.env` und `docker-compose.local.yml`
- `docker-compose.local.yml` ist in `.gitignore` und bleibt lokal erhalten
