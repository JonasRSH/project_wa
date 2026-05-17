# WA Generator

«WA Generator» ist eine modulare, containerisierte Webapplikation, umgesetzt mit Python und Django, die sowohl in Cloud-Umgebungen (z. B. IBM Cloud, Microsoft Azure, Google Cloud) als auch auf privaten Servern betrieben werden kann.

Die aktuelle Implementierung läuft als Docker-Container auf einem privaten Server (mein Raspberry Pi), öffentlich erreichbar unter wa-generator.jonashuggler.ch.

## Überblick

Die Anwendung dient zur automatisierten Erstellung eines Warenausweises (WA) aus PDF-Dokumenten. Der aktuelle Ansatz liest Daten aus PDF-Dateien wie Transitdokumenten (T1) und Warenausweisen zur Weiterverarbeitung aus. Die Anwendung kann mit Transitdokumenten und einer Abmeldeliste im PDF-Format ausprobiert werden.

Es handelt sich um keine fertige, einsatzbereite Version, sondern um eine Test- und Entwicklungsanwendung. Aktuell werden keine Daten in einer Datenbank gespeichert. Eine mögliche Weiterentwicklung wäre die Anbindung an eine Datenbank für Sendungsdaten sowie an eine Verzollungssoftware oder eine CH-Zoll-API für Dokumentendaten.

## Zentrale Vorteile

- **Hohe Portabilität:** Durch Docker-Containerisierung konsistent betreibbar über unterschiedliche Infrastrukturen
- **Skalierbarkeit:** Einfache horizontale und vertikale Skalierung in Cloud-Umgebungen
- **Schnelle Bereitstellung:** Kurze Deployments, reproduzierbare Setups und vereinfachtes Lifecycle-Management
- **Kosten- und Ressourceneffizienz:** Bedarfsorientierte Nutzung von Ressourcen, insbesondere in Cloud-Szenarien
- **Sicherheit & Isolation:** Klare Trennung der Anwendungskomponenten durch Container-Technologie

## Moderne Architekturmerkmale

- **Containerbasierter Betrieb (Docker):** Saubere Abhängigkeitstrennung und stabile Laufzeitumgebung
- **Flexibler Betrieb:** Wahlfreiheit zwischen Cloud-Betrieb und Betrieb auf eigenem Server
- **Erweiterbarkeit & Wartbarkeit:** Klare Struktur ermöglicht zukünftige Funktionserweiterungen und einfache Updates

Diese Architektur macht die Anwendung zu einer zukunftssicheren, flexibel einsetzbaren Webapplikation für professionelle Einsatzszenarien. Der «WA Generator» dient dabei als Beispiel. Mit denselben Tools können weitere Automatisierungen oder Anwendungen umgesetzt werden, die Mitarbeitende nicht ersetzen, aber ihre Arbeit erleichtern können.

## Funktionen

- Upload einer Abmeldeliste als PDF
- Extraktion und Aufbereitung der Sendungsdaten
- Anzeige einer Vorschau in der Weboberfläche
- Berechnung von Summen (Collies und Gewicht)
- Erzeugung einer Excel-Datei für den Warenausweis
- Login-geschützte Anwendung mit Admin-Bereich

## Projektstruktur

- `wa_automater/`: Django-Projekt (Settings, URLs, Apps, Templates, Static)
- `Python_Back_End/`: PDF-Parsing und fachliche Logik
- `requirements.txt`: Python-Abhängigkeiten
- `deploy/`: Beispielkonfigurationen für Deployment und Reverse Proxy

## Voraussetzungen

- Docker Desktop oder Docker Engine mit `docker compose`
- Optional für lokalen Betrieb ohne Docker: Python 3.10+ und `pip`

## Entwicklung mit Docker

Das lokale Entwicklungssetup ist der Standardweg. Du arbeitest im Projektordner, während der Container Django ausführt und den Quellcode über einen gemounteten Ordner nutzt.

Starten:

```bash
docker compose up --build
```

Danach im Browser öffnen:

- http://127.0.0.1:8000/

Stoppen:

```bash
docker compose down
```

### macOS-Hinweis

Wenn `docker compose up` mit einem Mount-Fehler unter `Documents` scheitert, braucht Docker Desktop Zugriff auf diesen Ordner. Gib Docker Desktop unter macOS Zugriff auf `Documents` oder verschiebe das Projekt in einen freigegebenen Ordner.

Sofortiger Fallback ohne Mount (ohne Live-Code-Sync):

```bash
docker compose -f docker-compose.dev-nomount.yml up --build
```

## Lokale Installation ohne Docker

Im Projekt-Root ausführen:

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

Danach im Browser öffnen:

- http://127.0.0.1:8000/

## Login und Admin

- Login-Seite: `/` oder `/login/`
- Admin: `/admin/`
- Hauptansicht nach Login: `/main/`
- Preview-Endpunkt: `/preview/`

## Entwicklung

Tests ausführen:

```bash
cd wa_automater
python3 manage.py test
```

## Deployment auf dem Raspberry Pi

1. Umgebungsdatei erstellen:

```bash
cp .env.pi.example .env.pi
```

2. In `.env.pi` Domain- und Security-Werte setzen:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_ALLOWED_HOSTS`
   - `DJANGO_CSRF_TRUSTED_ORIGINS`

3. Nur den WA-App-Container starten (lokal auf dem Pi unter Port 8081):

```bash
docker compose -f docker-compose.pi-app.yml --env-file .env.pi up -d --build
```

Wichtig für Benutzerkonten:

- Im Pi-Compose wird die SQLite-Datenbank in einem persistenten Docker-Volume gespeichert.
- Dadurch bleiben angelegte User inklusive Passwörter bei App-Updates erhalten.

4. Im bestehenden Webserver (z. B. Nginx) eine Subdomain auf `127.0.0.1:8081` proxyen.
   - Beispiel: `deploy/nginx-wa-automater.conf.example`
   - Falls dein zentraler Nginx selbst in Docker läuft, proxye stattdessen auf `http://host.docker.internal:8081` und ergänze im Nginx-Service `extra_hosts: ["host.docker.internal:host-gateway"]`

Nginx auf dem Pi aktivieren (Beispiel Debian/Raspberry Pi OS):

```bash
sudo cp deploy/nginx-wa-automater.conf.example /etc/nginx/sites-available/wa-automater
sudo ln -s /etc/nginx/sites-available/wa-automater /etc/nginx/sites-enabled/wa-automater
sudo nginx -t && sudo systemctl reload nginx
```

TLS-Zertifikat für die Subdomain erstellen (Certbot):

```bash
sudo mkdir -p /var/www/certbot
sudo certbot --nginx -d wa-generator.jonashuggler.ch
sudo systemctl reload nginx
```

5. Danach ist die Anwendung öffentlich erreichbar unter:

- wa-generator.jonashuggler.ch

Stoppen:

```bash
docker compose -f docker-compose.pi-app.yml --env-file .env.pi down
```

## Hinweise

- Beispiel-PDFs sind in `.gitignore` ausgeschlossen und werden nicht veröffentlicht.
- Die PDF-Auswertung ist von der Datenqualität in den Quelldokumenten abhängig.
- Dies ist eine noch nicht vollständig entwickelte Test-Version.
