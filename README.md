# WA Generator

«WA Generator» ist eine modulare, containerisierte Webapplikation, umgesetzt mit Python und Django, die sowohl in Cloud-Umgebungen (z. B. IBM Cloud, Microsoft Azure, Google Cloud) als auch auf privaten Servern betrieben werden kann.

Die aktuelle Implementierung läuft als Docker-Container auf einem privaten Server (mein Raspberry Pi), öffentlich erreichbar unter wa-generator.jonashuggler.ch.

## Überblick

Die Anwendung dient zur automatisierten Erstellung eines Warenausweises (WA) aus PDF-Dokumenten. Der aktuelle Ansatz liest Daten aus PDF-Dateien wie Transitdokumenten (T1) und Ladelisten zur Weiterverarbeitung aus. Die Anwendung kann mit Transitdokumenten und einer Abmeldeliste im PDF-Format ausprobiert werden.

Es handelt sich um keine fertige, einsatzbereite Version, sondern um eine Test- und Entwicklungsanwendung. Sendungsdaten, Collis und Transitdokumente werden in einer SQLite-Datenbank gespeichert und automatisch abgeglichen. Eine mögliche Weiterentwicklung wäre die direkte Anbindung an eine Verzollungssoftware oder eine CH-Zoll-API für Dokumentendaten.

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
- Upload und automatische Auswertung von T1-Transitdokumenten (MRN, Packstücke, Gewicht, Zollstelle)
- Automatischer Datenbankabgleich T1 ↔ Abmeldeliste mit Fehlerreport (Mengen-/Gewichtsabweichungen)
- Anzeige einer Vorschau in der Weboberfläche
- Berechnung von Summen (Collies und Gewicht)
- Erzeugung einer Excel-Datei für den Warenausweis mit Vorschau
- Login-geschützte Anwendung mit Admin-Bereich
- Automatisierte Tests (pytest für PDF-Parser, Django TestCase für Modelle und Abgleichlogik)