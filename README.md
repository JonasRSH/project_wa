# WA Automater

Webanwendung zur automatisierten Erstellung eines Warenausweises (WA) aus PDF-Dokumenten.
Das Projekt basiert auf Django und verarbeitet u. a. Abmeldelisten, um daraus strukturierte WA-Daten und eine Excel-Ausgabe zu erzeugen.

## Funktionen

- Upload einer Abmeldeliste als PDF
- Extraktion und Aufbereitung der Sendungsdaten
- Anzeige einer Vorschau in der Weboberflaeche
- Berechnung von Summen (Collies und Gewicht)
- Erzeugung einer Excel-Datei fuer den Warenausweis
- Login-geschuetzte Anwendung mit Admin-Bereich

## Projektstruktur

- `wa_automater/`: Django-Projekt (Settings, URLs, Apps, Templates, Static)
- `Python_Back_End/`: PDF-Parsing und fachliche Logik
- `requirements.txt`: Python-Abhaengigkeiten

## Voraussetzungen

- Docker Desktop oder Docker Engine mit `docker compose`
- Optional fuer lokalen Betrieb ohne Docker: Python 3.10+ und `pip`

## Entwicklung mit Docker

Das lokale Entwicklungssetup ist der Standardweg. Du codest im Projektordner, der Container fuehrt Django aus und nutzt den Quellcode ueber den gemounteten Ordner.

Starten:

```bash
docker compose up --build
```

Danach im Browser oeffnen:

- http://127.0.0.1:8000/

Stoppen:

```bash
docker compose down
```

macOS-Hinweis:
- Wenn `docker compose up` mit einem Mount-Fehler unter `Documents` scheitert, braucht Docker Desktop Zugriff auf diesen Ordner. Gib Docker Desktop unter macOS Zugriff auf `Documents` oder verschiebe das Projekt in einen bereits freigegebenen Ordner.
- Sofortiger Fallback ohne Mount (ohne Live-Code-Sync):

```bash
docker compose -f docker-compose.dev-nomount.yml up --build
```

## Lokale Installation ohne Docker

Im Projekt-Root ausfuehren:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Anwendung starten

```bash
cd wa_automater
python3 manage.py migrate
python3 manage.py runserver
```

Danach im Browser oeffnen:

- http://127.0.0.1:8000/

## Login und Admin

- Login-Seite: `/` oder `/login/`
- Admin: `/admin/`
- Hauptansicht nach Login: `/main/`
- Preview-Endpunkt: `/preview/`

Demo-Login (automatisch vorhanden in Docker-Setups):
- Benutzername: `test_user`
- Passwort: `test1234`

Hinweis zum Passwort-Verhalten:
- Wenn `test_user` bereits existiert, bleibt das bestehende Passwort unveraendert.
- Das Passwort aus `WA_DEMO_PASSWORD` wird nur bei Neuanlage gesetzt.
- Fuer einen erzwungenen Reset kann `WA_DEMO_FORCE_PASSWORD_RESET=true` gesetzt werden.

Hinweis zu Berechtigungen:
- Die Rollen des Demo-Users werden bei jedem Start synchronisiert.
- Standard: `is_staff=False` und `is_superuser=False` (kein Admin).
- Steuerbar ueber `WA_DEMO_IS_STAFF` und `WA_DEMO_IS_SUPERUSER`.

Die Demo-Zugangsdaten koennen per Umgebungsvariablen angepasst werden:
- `WA_DEMO_USERNAME`
- `WA_DEMO_PASSWORD`
- `WA_DEMO_EMAIL`
- `WA_DEMO_FORCE_PASSWORD_RESET`
- `WA_DEMO_IS_STAFF`
- `WA_DEMO_IS_SUPERUSER`

Falls noch kein Benutzer existiert:

```bash
cd wa_automater
python3 manage.py createsuperuser
```

## Entwicklung

Tests ausfuehren:

```bash
cd wa_automater
python3 manage.py test
```

## Docker auf Raspberry Pi (Test-Link ueber eigene Website)

Dieses Deployment ist vom lokalen Dev-Setup getrennt. Auf dem Pi laeuft nur das App-only Setup ueber [docker-compose.pi-app.yml](docker-compose.pi-app.yml) mit Gunicorn auf Host-Port 8081.

### Empfohlen bei bestehender Hauptseite auf dem Pi

1. Umgebungsdatei erstellen:

```bash
cp .env.pi.example .env.pi
```

2. In `.env.pi` Domain und Security-Werte setzen:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_ALLOWED_HOSTS`
	- `DJANGO_CSRF_TRUSTED_ORIGINS`

3. Nur den WA-App-Container starten (lokal auf dem Pi unter Port 8081):

```bash
docker compose -f docker-compose.pi-app.yml --env-file .env.pi up -d --build
```

Wichtig fuer Benutzerkonten:
- Im Pi-Compose wird die SQLite-Datenbank in einem persistenten Docker-Volume gespeichert.
- Dadurch bleiben angelegte User (inkl. Passwoerter) bei App-Updates erhalten.

4. Im bestehenden Webserver (z. B. Nginx) eine Subdomain auf `127.0.0.1:8081` proxyen.
	- Beispiel: `deploy/nginx-wa-automater.conf.example`
	- Falls dein zentraler Nginx selbst in Docker laeuft, proxye stattdessen auf `http://host.docker.internal:8081` und ergaenze im Nginx-Service `extra_hosts: ["host.docker.internal:host-gateway"]`.

Nginx auf dem Pi aktivieren (Beispiel Debian/Raspberry Pi OS):

```bash
sudo cp deploy/nginx-wa-automater.conf.example /etc/nginx/sites-available/wa-automater
sudo ln -s /etc/nginx/sites-available/wa-automater /etc/nginx/sites-enabled/wa-automater
sudo nginx -t && sudo systemctl reload nginx
```

TLS-Zertifikat fuer die Subdomain erstellen (Certbot):

```bash
sudo mkdir -p /var/www/certbot
sudo certbot --nginx -d wa-test.deine-domain.de
sudo systemctl reload nginx
```

5. Auf deiner Hauptseite einfach auf die Subdomain verlinken, z. B. `https://wa-test.deine-domain.de`.

Stoppen:

```bash
docker compose -f docker-compose.pi-app.yml --env-file .env.pi down
```

Hinweis:
- Ohne `.env.pi` starten die Compose-Dateien jetzt mit Fallback-Werten fuer den Testserver. Fuer den Produktivbetrieb solltest du die Datei trotzdem anlegen und Domain-/Secret-Werte explizit setzen.

## Hinweise

- Beispiel-PDFs sind in `.gitignore` ausgeschlossen und werden nicht veroeffentlicht.
- Die PDF-Auswertung ist von der Datenqualitaet in den Quelldokumenten abhaengig.


## VERSION

Dies ist eine nicht zuende entwickelte Test-Version.