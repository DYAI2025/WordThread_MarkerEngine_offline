# Funktionsanalyse der WordThread Marker Engine

## 1. Systemübersicht
Die WordThread Marker Engine ist eine deterministische Analyse-Pipeline für mehrsprachige Gesprächsdaten. Sie kombiniert regelbasierte Marker-Erkennung, evidenzbasierte Aktivierung, gewichtetes Scoring und Drift-Überwachung zu einem reproduzierbaren Ergebnis-Set. Der aktuelle Offline-Stand bündelt Kernmodule, API-Server und Hilfswerkzeuge in einer gemeinsamen Codebasis, sodass analytische Teams die Engine lokal evaluieren, erweitern und für Produktivzwecke vorbereiten können.

## 2. Architektur und Hauptkomponenten
### 2.1 MarkerEngine (Kernel)
Der Kern (`marker_engine_core.py`) lädt beim Start Marker, Schemata, Detektoren und Plugins aus den bereitgestellten Artefakten. Zentrale Aufgaben:
- **Ressourcen-Management:** Marker-Definitionen (`_Marker_5.0/*.yaml`), Schema-Dateien (`schemata/*.json`) und die Detektor-Registry (`DETECT_/DETECT_registry.json`) werden in interne Caches überführt. Der Master-Schema-Eintrag steuert aktive Schemata, Prioritäten und den Fusionsmodus.
- **Detektionsphase:** Für jeden Text werden erst registrierte Detektoren abgearbeitet (Regex-Dateien, Plugin-Aufrufe, kundenspezifische Module wie `NumericNormalizerPlugin`). Anschließend folgen musterbasierte Atom-Marker (`ATO_*`).
- **Analyse-API:** `analyze(text, hits=None)` verarbeitet freie Texte, während `analyze_conversation(messages, window, options)` Dialoge in Sliding-Window-Chunks zerlegt, Treffer evidenzbasiert aggregiert und das Ergebnis in einem strukturierten Dict mit `hits`, `aggregates`, `scores` und `drift` zurückgibt.

### 2.2 Aktivierungs- und Evidenzlogik
Marker-Definitionen mit `activation`-Block werden nach Abschluss der primären Erkennung ausgewertet. Unterstützte Regeln (u. a. `ANY`, `ALL`, `AT_LEAST`, `WEIGHTED_AND`, `X_OF_Y`, `SUM_WEIGHT`, `AT_LEAST_DISTINCT`, `FREQUENCY`) bilden komplexe Verhaltensmuster ab. Für jedes aktivierte Konstrukt werden Evidenzlisten, Parameter und Ursprungsregeln persistiert, wodurch eine nachvollziehbare Treffer-Hierarchie entsteht.

### 2.3 ScoringEngine
Die `ScoringEngine` kapselt gewichtete Bewertungsmodelle (`scoring_engine.py`). Standardmäßig enthalten sind:
- **Manipulations-Index:** skaliert Marker aus den Kategorien Manipulation, Gaslighting, Emotional Abuse, Fraud etc.
- **Beziehungsgesundheit:** positive Marker erhöhen, toxische Marker senken den Score; inverse Skala.
- **Fraud-Wahrscheinlichkeit:** vierstufige Thresholds (low–critical) mit starkem Gewicht auf Fraud- und Financial-Abuse-Marker.
- **Kommunikationsqualität:** hebt empathische, unterstützende und boundary-setting Marker hervor.

Die Engine bildet Text in `TextChunk`-Instanzen ab, gruppiert `MarkerMatch`-Objekte nach Chunk, normalisiert die Scores auf eine 1–10-Skala, berechnet Trends, Verteilungen, Sprecher-Splits und Alerts. Ergebnisse landen in `ScoringResult` samt `chunk_scores`, `aggregated_scores`, `speaker_scores`, `timeline` und `summary`.

### 2.4 DriftAxesManager
`drift_axes.py` liefert ein konfigurationsbasiertes Mapping, das aggregierte Scores (z. B. Relationship Health, Manipulation Index, Fraud Probability) in Drift-Werte überführt. Schwellenwerte für Warn- und Kritikal-Stufen triggern `DriftEvent`-Objekte mit Zeitstempel, Richtung und Metadaten. Die Methode `calculate_drift_values` multipliziert Scores mit Achsen-Gewichten, `check_thresholds` prüft Richtungen (`above`, `below`) und verwaltet aktive Events.

### 2.5 API Service
`api_service.py` exponiert die Engine über FastAPI. Wesentliche Endpunkte:
- `POST /analyze`: komplette Pipeline inkl. Scoring und Drift, Ausgabe als `AnalysisResponse` mit Hash-basierter Artefaktablage.
- `GET /scores`: aktive Bewertungsmodelle und Timestamp.
- `GET /drift`: Drift-Achsen samt aktuell ausgelöster Events.
- `GET /health`: Health-Check mit Versionsangabe.
- `GET /artifacts/{input_hash}`: Reproduktion früherer Läufe.
Ein Lifecycle-Manager initialisiert Engine und Drift-Manager beim Start. CORS-Origins sind konfigurierbar.

### 2.6 Zusatzmodule und Plugins
- **NumericNormalizerPlugin:** Beispiel für kundenspezifische Normalisierung.
- **Engine Digest:** `engine_digest.py` erzeugt SHA-256-Digests über Marker, Detector-Registry, Python-Sourcen und Requirements zur Release-Nachvollziehbarkeit.
- **Validierungswerkzeuge:** `validate_system.py` prüft Referenzintegrität, Aktivierungsformate und deterministische Ergebnisse.

## 3. Mechanik des Analyseprozesses
1. **Ingestion:** Gespräche bestehen aus Nachrichtenobjekten (`id`, ISO-8601-Zeitstempel `ts`, Sprecherkennung, freier Text).
2. **Windowing:** `analyze_conversation` erstellt überlappungsfähige Fenster. Kleine Restfenster unterhalb halber Fenstergröße werden verworfen.
3. **Primärerkennung:** Detektoren aus der Registry laufen priorisiert; plugin-basierte Module können eigene Trefferlisten liefern. Anschließend prüft das System atomare Pattern-Marker.
4. **Aktivierung & Evidenz:** Komplexe Marker aggregieren Primärtreffer gemäß Regelwerk. Evidenzverweise (Message-IDs, Parameter) ermöglichen Audits.
5. **Scoring & Aggregation:** Rohscores pro Marker werden nach Schema-Prioritäten fusioniert. Zusätzliche Metriken entstehen im ScoringAdapter/ScoringEngine.
6. **Drift-Analyse:** Aggregierte Scores werden mit Achsengewichten verrechnet, Schwellen triggern Events.
7. **Output-Serialisierung:** Treffer werden auf Nachrichten gemappt, Scores zusammengefasst, Drift-Daten (Zeitachsen, Werte) berechnet und zusammen mit Timestamp und optionaler Zusammenfassung zurückgegeben.

## 4. Ein- und Ausgabespezifikation
### 4.1 Eingaben (Kernel & API)
| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `messages` | Liste von Objekten | Pflicht. Jedes Objekt benötigt `id` (String), `ts` (ISO-8601), `speaker` (String) und `text` (String). |
| `window` | Dict | Optional. Standard `{ "size": 30, "overlap": 0 }`. Steuert Sliding-Window-Größe und Überlappung. |
| `options` | Dict | Optional. Beispiel `{ "locale": "de-DE", "timezone": "Europe/Berlin" }`. Kann zur Internationalisierung genutzt werden. |

### 4.2 Ausgaben des Kernels (`MarkerEngine.analyze_conversation`)
| Schlüssel | Inhalt |
| --- | --- |
| `hits` | Liste strukturierter Treffer: `marker_id`, zugehörige `message_id`, placeholder `score`. Aktivierte Marker enthalten optional `evidence`, `rule`, `params`. |
| `aggregates` | Häufigkeiten pro Marker-ID über alle Fenster. |
| `scores` | derzeit einfacher Intensitätswert (`overall_intensity`) basierend auf Trefferanzahl. |
| `drift` | Dict mit `timestamps` (Liste) und `values` (Histogramm bzw. kumulative Intensität). |

### 4.3 API-Antwort (`AnalysisResponse`)
| Feld | Beschreibung |
| --- | --- |
| `timestamp` | UTC-ISO-Zeitstempel des API-Laufs. |
| `summary` | Kurzbeschreibung aus dem Analyseergebnis (Platzhalter, kann leer sein). |
| `hits` | Trefferliste inkl. Evidenzinformationen. |
| `scores` | Übernommene Scores aus dem Engine-Ergebnis bzw. dem ScoringAdapter. |
| `drift_values` | Aggregierte Drift-Kennzahlen je Achse. |
| `drift_events` | Liste ausgelöster `DriftEvent`-Objekte mit Schwellen und Richtung. |
| `engine_digest` | SHA-256-Digest der Engine-Konfiguration für Audit-Trails. |

## 5. Release- und Qualitätstests
Für eine Release-Freigabe werden folgende Testebenen empfohlen:
1. **Unit- und Systemtests:** `python -m pytest` im Verzeichnis `ME_ENGINE_CORE_V0.9/marker_engine_core_v09`. Deckt Kernlogik, Aktivierung, Scoring, Drift und Determinismus ab.
2. **Deterministische Validierung:** `python validate_system.py` prüft Marker-/Detektor-Referenzen, Aktivierungsformate und deterministische Wiederholbarkeit.
3. **API Smoke-Test (optional):** Start des FastAPI-Servers (`uvicorn api_service:app --reload`) und Aufruf der Endpunkte `/health` und `/analyze` mit Beispieldaten.
4. **Digest-Erzeugung:** `python engine_digest.py` dokumentiert den Zustand der Engine-Artefakte für Compliance.

Die Tests erzeugen klare ✅/❌-Ausgaben und sollten vor jedem Releaselauf automatisiert werden.

## 6. Erweiterbarkeit und Betriebsaspekte
- **Marker & Detektoren:** Neue YAML-Marker können ergänzt, Plugins über die Registry eingebunden werden. Die interne Plugin-Ladepipeline akzeptiert modulare Python-Dateien.
- **Scoring-Modelle:** Anpassungen an Gewichtungen, Thresholds oder neuen ScoreTypes erfolgen in `ScoringEngine._initialize_default_models`. Eigene Modelle lassen sich über die `models`-Map registrieren.
- **Drift-Achsen:** Erweiterungen der Achsen-Definitionen (inkl. Schwellen) erfolgen zentral im `DriftAxesManager` bzw. über externe Konfigurationsdateien.
- **API & Deployment:** Der FastAPI-Server ist CORS-konfigurierbar, Artefakte werden optional im Dateisystem persistiert. Containerisierung ist über das vorhandene Dockerfile vorbereitet.

## 7. Weiterführende Ressourcen
- Detail-README innerhalb von `ME_ENGINE_CORE_V0.9/marker_engine_core_v09`
- Sphinx-Dokumentation (`docs/` im Modulverzeichnis) für Entwickler*innen
- Validierungs- und Benchmark-Skripte (`validate_system.py`, `engine_digest.py`)
