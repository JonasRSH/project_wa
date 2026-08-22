#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Docker Compose wurde nicht gefunden. Bitte Docker + Compose installieren."
    exit 1
fi

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "'.env' wurde aus '.env.example' erstellt. Bitte Werte eintragen und Script erneut starten."
        exit 1
    else
        echo "'.env' fehlt und '.env.example' wurde nicht gefunden."
        exit 1
    fi
fi

echo "Starte Build und Container..."
COMPOSE_FILES="-f docker-compose.yml"
if [ -f docker-compose.local.yml ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.local.yml"
    echo "Lokales Override erkannt: docker-compose.local.yml"
fi

$COMPOSE_CMD $COMPOSE_FILES up -d --build

echo "Migrations und Static-Files fuer website..."
$COMPOSE_CMD $COMPOSE_FILES exec -T website python manage.py migrate
$COMPOSE_CMD $COMPOSE_FILES exec -T website python manage.py collectstatic --noinput

echo "Migrations und Static-Files fuer wa-generator..."
$COMPOSE_CMD $COMPOSE_FILES exec -T wa-generator python manage.py migrate
$COMPOSE_CMD $COMPOSE_FILES exec -T wa-generator python manage.py collectstatic --noinput

echo "Container-Status:"
$COMPOSE_CMD $COMPOSE_FILES ps

echo "Update abgeschlossen."
