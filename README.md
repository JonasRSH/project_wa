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

- Python 3.10+
- `pip`

## Installation

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

## Docker

Container bauen und starten:

```bash
docker compose up --build
```

Die Anwendung ist danach unter http://127.0.0.1:8000/ erreichbar.

Container stoppen:

```bash
docker compose down
```

## Docker auf Raspberry Pi (Test-Link ueber eigene Website)

Dieses Setup startet die App auf dem Pi mit Gunicorn und Caddy (HTTPS + Reverse Proxy).

Wenn deine Hauptseite bereits auf demselben Pi laeuft, nutze stattdessen das App-only Setup ohne zweiten Reverse Proxy auf Port 80/443.

### Empfohlen bei bestehender Hauptseite auf dem Pi

1. Umgebungsdatei erstellen:

```bash
cp .env.pi.example .env.pi
```

2. In `.env.pi` Domain und Security-Werte setzen:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_ALLOWED_HOSTS`
	- `DJANGO_CSRF_TRUSTED_ORIGINS`

3. Nur den WA-App-Container starten (lokal auf dem Pi unter Port 18000):

```bash
docker compose -f docker-compose.pi-app.yml --env-file .env.pi up -d --build
```

4. Im bestehenden Webserver (z. B. Nginx) eine Subdomain auf `127.0.0.1:18000` proxyen.
	- Beispiel: `deploy/nginx-wa-automater.conf.example`

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

### Alternative: Vollsetup mit eigenem Caddy

Nur verwenden, wenn auf dem Pi noch kein anderer Dienst Ports 80/443 belegt.

1. DNS-Link auf deiner Domain anlegen:
	- Erstelle auf deiner Website/Domain einen Subdomain-Eintrag, z. B. `wa-test.deine-domain.de`.
	- Setze einen `A`-Record auf die oeffentliche IP deines Raspberry Pi (oder Routers).
2. Router-Portfreigabe einrichten:
	- Leite `80` und `443` auf den Raspberry Pi weiter.
3. Umgebungsdatei fuer Pi erstellen:

```bash
cp .env.pi.example .env.pi
```

4. Werte in `.env.pi` anpassen:
	- `DOMAIN`
	- `DJANGO_SECRET_KEY`
	- `DJANGO_ALLOWED_HOSTS`
	- `DJANGO_CSRF_TRUSTED_ORIGINS`
5. Container auf dem Pi starten:

```bash
docker compose -f docker-compose.pi.yml --env-file .env.pi up -d --build
```

6. Test im Browser:
	- `https://wa-test.deine-domain.de`

Stoppen:

```bash
docker compose -f docker-compose.pi.yml --env-file .env.pi down
```

Hinweis:
- Wenn deine Website bei GitHub Pages liegt, kann sie nicht direkt reverse-proxyen.
- Nutze in dem Fall einen Subdomain-DNS-Eintrag, der auf den Pi zeigt (wie oben beschrieben).

## Hinweise

- Beispiel-PDFs sind in `.gitignore` ausgeschlossen und werden nicht veroeffentlicht.
- Die PDF-Auswertung ist von der Datenqualitaet in den Quelldokumenten abhaengig.


## VERSION

Dies ist eine nicht zuende entwickelte Test-Version.