# WA_Generator 1.0

## Einleitung

WA steht für Warenausweis. Ein Warenausweis wird für den LKW-Verkehr von Waren, z. B. über die Schweizerisch-Deutsche Grenze, benötigt. Er ist eine strukturierte Auflistung aller Transitdokumente (mit Transit-/MRN-Nummer, Packstückanzahl und -art, Warenbezeichnung und Gewicht) zu den Sendungen, die der LKW geladen hat.

Das manuelle Erstellen eines Warenausweises kann je nach Anzahl der Transitdokumente sehr zeitaufwendig sein. Daher ist eine automatisierte Erstellung durch eine Anwendung besonders hilfreich. WA_Generator 1.0 ist der erste Versuch, dies mit Python und einer HTML-basierten Oberfläche zu realisieren.

## Funktionsweise

Die Webapplikation ermöglicht:
- Automatisiertes Auslesen und Verarbeiten von Transitdokumenten
- Generierung eines Warenausweises als Excel-Datei
- Vorschau des Warenausweises direkt im Browser
- Download der generierten Excel-Datei nach Prüfung

## Aufbau des Warenausweises

Der Warenausweis enthält oben das Datum des Abfertigungstages, den Grenzübergang, das LKW-Kennzeichen und eine Auflistung der Transitdokumente.

Die Transitdokumente werden sortiert dargestellt:
- Oben: Durchgehende Transitdokumente, die bis ins Empfangsland ausgestellt sind
- Angabe der Abgangszollstelle und Vermerk: "DE Zoll A-Nummer siehe Position a-z"
- Unten: Transitdokumente, die an der Grenze erledigt werden, für Sendungen, welche an der Grenze einfuhrverzollt    werden

## Benötigte Software

- Python 3
- Django
- Beliebiger Webbrowser
- Abhängigkeiten: PyPDF2, pandas, openpyxl, re

## Installation

### Lokale Installation (Entwicklung)

1. Repository klonen oder Dateien herunterladen:
   ```sh
   git clone <REPO-URL>
   cd <Projektordner>
   ```
2. (Optional, empfohlen) Virtuelle Umgebung anlegen und aktivieren:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Abhängigkeiten installieren:
   ```sh
   pip install -r requirements.txt
   ```
4. Django-Migrationen durchführen:
   ```sh
   python3 manage.py migrate
   ```
5. Entwicklungsserver starten:
   ```sh
   python3 manage.py runserver 0.0.0.0:8000
   ```
6. Im Browser öffnen: [http://127.0.0.1:8000/]

### Produktivbetrieb (Empfohlen für Server)

1. Voraussetzungen:
   - Python 3.x
   - pip
   - Webserver (z. B. Nginx oder Apache)
   - Gunicorn (WSGI-Server)

2. Schritte:
   1. Wie oben: Repository klonen, virtuelle Umgebung anlegen, Abhängigkeiten installieren, Migrationen durchführen.
   2. Gunicorn installieren (falls nicht enthalten):
      ```sh
      pip install gunicorn
      ```
   3. Gunicorn-Server starten:
      ```sh
      gunicorn wa_automater.wsgi:application --bind 0.0.0.0:8000
      ```
   4. (Optional) Nginx als Reverse Proxy einrichten:
      - Beispiel-Konfiguration siehe [Nginx-Dokumentation](https://docs.gunicorn.org/en/stable/deploy.html#nginx-configuration)
      - Statische Dateien ggf. mit `python3 manage.py collectstatic` sammeln

3. Datenbank-Backup und -Wartung regelmäßig durchführen.

#### Beispiel für Gunicorn-Start (Produktiv):
```sh
gunicorn wa_automater.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

#### Beispiel für Nginx-Proxy (Ausschnitt):
```
server {
    listen 80;
    server_name example.com;

    location /static/ {
        alias /pfad/zum/projekt/wa_automater/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Test der Webapplikation

1. Im Projektverzeichnis folgenden Befehl ausführen:
   ```sh
   python3 manage.py runserver
   ```
2. Im Browser öffnen:
   http://127.0.0.1:8000/

## Bedienung

- Über die Weboberfläche können relevante Daten eingegeben und Dokumente hochgeladen werden.
- Mit Klick auf „WA Generieren“ wird der Warenausweis erstellt und als Tabelle angezeigt.
- Nach Prüfung kann die Excel-Datei über „Excel herunterladen“ (noch nicht programmiert) gespeichert werden.

## Hinweise

- Die Anwendung befindet sich im Prototyp-Stadium und kann weiterentwickelt werden.
- Für produktiven Einsatz sind weitere Prüfungen und Anpassungen notwendig.

## Administration

Es existiert ein für Testzwecke angelegter Administrator:
- User: test_user
- Passwort: tekTef-4tonqu-fukmud

Dieser muss bei Installation aus Sicherheitsgründen gelöscht und ein neuer User mit sicherem Passwort eingerichtet werden.