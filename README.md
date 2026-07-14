# WA Generator

«WA Generator» ist eine modulare, containerisierte Webapplikation, umgesetzt mit Python und Django, die sowohl in Cloud-Umgebungen (z. B. IBM Cloud, Microsoft Azure, Google Cloud) als auch auf privaten Servern betrieben werden kann.

Die aktuelle Implementierung läuft als Docker-Container auf einem privaten Server (mein Raspberry Pi), öffentlich erreichbar unter wa-generator.jonashuggler.ch.

## Überblick

Die Anwendung dient zur automatisierten Erstellung eines Warenausweises (WA) aus PDF-Dokumenten. Der aktuelle Ansatz liest Daten aus PDF-Dateien wie Transitdokumenten (T1) und Ladelisten zur Weiterverarbeitung aus. Die Anwendung kann mit Transitdokumenten und einer Abmeldeliste im PDF-Format ausprobiert werden.

Es handelt sich um keine fertige, einsatzbereite Version, sondern um eine Test- und Entwicklungsanwendung. Aktuell werden keine Daten in einer Datenbank gespeichert. Eine mögliche Weiterentwicklung wäre die Anbindung an eine Datenbank für Sendungsdaten sowie an eine Verzollungssoftware oder eine CH-Zoll-API für Dokumentendaten.
Eine eigene Datenbank mit SQL zum Datenabgleich der verschiedenen Dokumente ist vorbereitet.

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



## Anwendung starten

```bash
cd wa_automater
python3 manage.py migrate
python3 manage.py runserver
```

Danach im Browser öffnen:

- http://127.0.0.1:8000/