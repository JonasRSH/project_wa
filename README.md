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

## Hinweise

- Beispiel-PDFs sind in `.gitignore` ausgeschlossen und werden nicht veroeffentlicht.
- Die PDF-Auswertung ist von der Datenqualitaet in den Quelldokumenten abhaengig.


## VERSION

Dies ist eine nicht zuende entwickelte Test-Version.