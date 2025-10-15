Projekt Warenausweis (WA)

Pflichtenheft / Software Requirements Specification (SRS)

Die Software soll eine browserbasierte Anwendung sein, entwickelt mit Python, Django und einer HTML/CSS-Oberfläche. Ihr Hauptzweck ist die automatische Generierung eines Warenausweises aus bereitgestellten Daten. Zusätzlich soll ein Kontrollabgleich zwischen einer Liste von Sendungen (Abmeldeliste) und den vorhandenen Transitdokumenten erfolgen, wobei Abweichungen und Fehler angezeigt werden.

Der generierte Warenausweis soll im Browser zur Sichtprüfung angezeigt werden. Ein Download des Warenausweises als Excel-Datei muss möglich sein. Der Warenausweis soll außerdem direkt an eine vordefinierte E-Mail-Adresse gesendet werden, inklusive der zugehörigen Transitdokumente als Anhang. Eine kleine SQL-Datenbank soll zur Speicherung von Daten wie LKW-Kennzeichen und Grenzübergängen implementiert werden.

**Funktionale Anforderungen:**

1. Das Warenausweis-Datum kann über ein Feld „Datum des Warenausweises“ ausgewählt werden.
2. LKW-Liste mit Kennzeichen und Abfahrtsorten (kann in den „Einstellungen“ vordefiniert werden).
3. Auswahlliste für Grenzübergänge (kann vordefiniert und über Dropdown erweitert werden).
4. Auswahl des Zollamts beim Abgang (kann vordefiniert und über Dropdown erweitert werden).
5. Uhrzeit der Ankunft an der Grenze kann ausgewählt werden (vor 19:00 / nach 19:00 Uhr).
6. Auswahl der Abmeldeliste als PDF-Datei oder über API/ODBC/JDBC-Schnittstelle zum Auslesen der Daten aus AS400/IBM i DB2-Datenbank.
7. Auswahl der T1-Dokumente als PDF-Dateien zur Abmeldeliste (z. B. Download aus Postkorb) oder via API aus Zollsoftware oder Website CH   Zoll.
8. Hintergrundabgleich der Abmeldeliste und T1-Dokumente.
9. Anzeige des generierten Warenausweises auf dem Bildschirm zur Sichtprüfung.
10. Bei fehlenden Daten: Anzeige von Fehlermeldungen, z. B. „Position 3, 11, 45 der Abmeldeliste hat keine Beschriftung / T1 fehlt zu Position 7, 12, 23, etc.“.
11. Zu prüfende Fehler:
    - Gibt es zu jeder Sendung mit Beschriftung E-T1 ein T1-Dokument?
    - Sind alle Sendungen mit Beschriftung S-T1 oder GVZ auf dem S-T1 enthalten?
    - Stimmt die Gesamtzahl der Sendungen? Optional: Gewichts- und Colliabgleich.
12. Wenn keine Fehler gefunden werden: Ausgabe/Download des Warenausweises als Excel-Datei oder direkte Weiterleitung per Button an eine vordefinierte E-Mail-Adresse (z. B. zoll-basel@spedition.ch).

**Nicht-funktionale Anforderungen:**

- Die Anwendung soll benutzerfreundlich und responsiv sein.
- Datensicherheit und Datenschutz müssen gewährleistet sein, insbesondere für hochgeladene Dokumente und sensible Daten.
- Das System soll für zukünftige Anforderungen erweiterbar sein (z. B. weitere Dokumenttypen, neue Prüfregeln).
- Fehlermeldungen sollen für den Nutzer klar und nachvollziehbar sein.

**Optionale Features:**
- Protokollierung aller Aktionen und Fehler zu Prüfzwecken.
- Mehrsprachigkeit (Deutsch/Englisch/Französisch).
- Rollenbasierte Zugriffskontrolle für verschiedene Nutzergruppen.

**Nachteile und Problematik**
Das auslesen von Daten aus PDF Dateien kann eine Schwierigkeit darstellen. Die von "Hand" erfassten Daten können für das Auslesen falsch formatiert oder Schreibfehler enthalten, so dass das Programm dei Daten nicht korrekt auswerten kann. Die Qualität der Auswertung ist stark abhängig von der genauen Datenerfassung.