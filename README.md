# WordThread MarkerEngine Offline

## Die Conversational Intelligence, die toxische Muster sichtbar macht
WordThread MarkerEngine übersetzt komplexe Dialoge in belastbare Risiko- und Chancenprofile. Der Offline-Stack liefert Ihnen eine sofort einsatzbereite Umgebung, um Marker-Modelle zu validieren, Scoring-Strategien zu verfeinern und Drift frühzeitig zu erkennen – ganz ohne Cloud-Anbindung.

## Warum führende Teams auf WordThread setzen
- **Deterministischer Motor:** Reproduzierbare Ergebnisse dank regelbasierter Erkennung, klar definierter Aktivierungslogik und versionierter Artefakte.
- **360°-Bewertung:** Vier integrierte Score-Layer (Manipulation, Beziehungsgesundheit, Fraud, Kommunikationsqualität) beleuchten Risiken und Schutzfaktoren zugleich.
- **Explainable Insights:** Evidenzketten, Drift-Ereignisse und Engine-Digests sorgen für Audit-Fähigkeit und Compliance.
- **Bereit für Produktivbetrieb:** FastAPI-Service, Docker-Setup und Validierungsskripte ermöglichen einen direkten Übergang in gesicherte Produktionsumgebungen.

## Kernfunktionen im Überblick
1. **Marker Detection & Activation** – Priorisierte Detektoren (Regex, Plugins, Custom) plus komplexe Aktivierungsregeln für zusammengesetzte Muster.
2. **Scoring Engine** – Gewichtete Modelle mit Trendanalysen, Sprecher-Splits und Alerting für kritische Schwellen.
3. **Drift Monitoring** – Mehrdimensionale Drift-Achsen messen Eskalationen oder Stabilisierung in Echtzeit.
4. **API & Artefaktverwaltung** – `/analyze`, `/scores`, `/drift`, `/health` und Artefakt-Abruf für vollständige Nachvollziehbarkeit.

## Typische Einsatzfelder
- **Trust & Safety:** Messenger-, Dating- oder Community-Plattformen erkennen Manipulation, Betrug und Eskalationen frühzeitig.
- **Customer Experience:** Service-Teams analysieren Konflikte, Empathie und Beziehungsgesundheit in Support-Gesprächen.
- **Compliance & Audit:** Finanz- oder Versicherungsdienstleister dokumentieren regulatorisch relevante Gesprächsmuster.
- **Produktentwicklung:** Conversational-AI-Teams testen schnell neue Marker oder Score-Modelle im Offline-Setup.

## Was im Offline-Paket steckt
- Vollständiger Engine-Kern inklusive Marker-, Schema- und Detector-Artefakten.
- FastAPI-Service mit CORS-Steuerung und Hash-basiertem Artefakt-Storage.
- Scoring- und Drift-Layer inklusive vorkonfigurierter Modelle.
- Validierungs-, Test- und Digest-Skripte für Release-Freigaben.
- Ausführliche Funktionsanalyse unter [`docs/Funktionsanalyse.md`](docs/Funktionsanalyse.md).

## Schnellstart
1. Repository klonen und Python-Umgebung aktivieren.
2. Abhängigkeiten installieren: `pip install -r ME_ENGINE_CORE_V0.9/marker_engine_core_v09/requirements.txt`.
3. Validierung & Tests ausführen:
   - `python -m pytest` (im Engine-Verzeichnis)
   - `python validate_system.py`
4. API starten: `uvicorn api_service:app --host 0.0.0.0 --port 8000`.
5. Analyse anstoßen: Beispiel-Conversation an `POST /analyze` senden und Drift-Alerts live verfolgen.

## Qualität, die Vertrauen schafft
- Deterministische Output-Prüfung, Referenzvalidierung und Aktivierungs-Checks sind integriert.
- Engine-Digests dokumentieren jeden Release-Stand per SHA-256.
- Drift-Events liefern unmittelbare Signale für Risiko- und Stabilitätsänderungen.

## Nächste Schritte
Bereit, Konversationen neu zu verstehen? Nutzen Sie die Offline-Edition, um Use-Cases zu testen, und skalieren Sie anschließend mit dem WordThread Platform-Team in Ihre Zielumgebung. Kontaktieren Sie uns für maßgeschneiderte Marker-Entwicklung, Integrationssupport und Enterprise-SLAs.
