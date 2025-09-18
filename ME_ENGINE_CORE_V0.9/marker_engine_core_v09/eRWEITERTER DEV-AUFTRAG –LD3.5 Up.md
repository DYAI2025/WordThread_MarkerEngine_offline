### ERWEITERTER DEV-AUFTRAG – Upgrade auf Lean-Deep 3.5 (runtime only, schema-kompatibel zu 3.4, ENGINE_PROTO 3)
**Ziel**
- Die bestehende Transcriber-Lösung (TWE Core) wird auf Lean-Deep 3.5 erweitert. Ziel ist eine schema-kompatible Migration zu 3.4 ohne Änderungen am Marker-Schema. Upgrades erfolgen lediglich auf Logik-Ebene: Engine, Detektoren, Konfiguration (inkl. Domänen-Priorisierung: Therapy → Informal → Leadership → Support) und API (neue bzw. erweiterte Endpunkte). Qualität ist definiert als lauffähige runtime-Funktion mit sichtbar verwertbarem Output.
**Fixierte Entscheidungen / Rahmen**
- Keine Schemaänderungen an existierenden Markern; nur Engine-Logik, Detektoren und APIs werden erweitert.
- Artifacts: PII-minimals Telemetry-Snapshots, Retention 30 Tage.
- Sprachen: DE+EN parallel, alle IDs/Dateien/Marker-Namen Englisch.
**Kompatibilität & Basis**
- Vier-Ebenen-Architektur ATO→SEM→CLU→MEMA und Intuitionslogik (CLU-basiert, 3.4) bleiben unverändert. Marker-YAMLs und Mongo-Collections (Definitions- und Runtime-Events) unverändert, Loader wie gehabt. Ein Baseline-Hook wird zwischen SEM und CLU rein runtimeseitig eingeschleust.
- Scoring-Fenster und Aggregation mit Decay bleiben kompatibel und werden um Multipliers und Rampen-Wächter ergänzt. Markervorlagen bleiben als Referenz bestehen.
**Upgrade-Delta LD-3.5**
- Neue Pipeline: Messages → ATO → SEM → [NEU Baseline-Hook] → CLU → MEMA.
- Neue Runtime-Module zwischen SEM und CLU: Baseline (8 Features: TTB, RLD, YIR, IQP, NMD, ARP, IAD, CONG pro 100T, DE+EN), Heat-FSM (STABLE/WARMING/HOT/COOLDOWN), TTL-Multipliers (familienbasiert, capped), Frequency-Layer (FFT auf CONG/IAD/RLD, 6-8 Turns), Ramp-Guard+MEF+Stop-Delay, Backstop+Evidence-Buffer.
- Intuitionslogik bleibt CLU-basiert und wird durch Baselines ergänzt, nicht ersetzt.
**P0 – Must-Have:**
- Baseline-Schicht/Features, Gating, API-Endpunkt /baselines (Read-only, liefert letzten BSL-Block pro Turn)
- Priorisierung nach Domäne (Therapy → Informal → Leadership → Support) mit spezifischen Heuristiken je Domäne (Priors).
- Boot-Phase: RLD greift nicht in T1/T2; IQP v2/Kombinierte Triggerlogik
- Logging von two-levels-red (Abweichungen auf Micro+Domain-Ebene)
**P1 – Strong-Value:**
- Heat-FSM (zustandsbasiert, stabil reproduzierbar, kein HOT in Boot)
- 5 Runtime-Events (silent_spike, question_overhang, imperative_burst, congruence_break, withdrawal) mit Textvorschlägen im Analyseoutput
- Multipliers TTL-stabil, sichtbar; Scores bleiben normiert, stabil
- API /heat sichtbar
**P2 – Stabilität/Frühwarnung:**
- FFT für CONG/IAD/RLD (Peaks, 2–6 Taktungen erkannt)
- Rampen-Wächter, Stop-Delay, Backstop (3 Levels)
- Zeit/Frequenz-Audit via /spec, /backstop Endpoints
**P3 – Ops & Compliance:**
- Telemetry-Artifacts via /artifacts/{hash}, PII-minimal, 30 Tage Retention
- DE/EN-Lexika für Pronomen/Negation, Language-Auto-Detect
- Registry- und Doku-Erweiterung (DETECT_registry.json auf Version 3.5, neue Klassen eintragen, CHANGELOG/Readme)
- CI/Gate: Priors-Datei valid, p/100T Normierung, support_k ≥3
**Wichtige Artefakte und Schnittstellen**
- Konfiguration: `config/baselines.json` (inkl. Priors, Gating-Optionen, Ramp, Multiplier)
- Neue/erweiterte Module: `engine/baselines/store.py`, `engine/baselines/features.py`, `engine/pipeline/hook_baselines.py`, `engine/runtime/heat_fsm.py`, `engine/runtime/events.py`, `engine/runtime/multiplier_policy.py`, `engine/baselines/fft.py`, `engine/runtime/ramp_guard.py`, `engine/monitor/backstop.py`, `engine/actions/buffer.py`, `api_service.py` (neue Endpoints)
- Registry-Anpassung: `DETECT_registry.json` auf "3.5"
**Akzeptanz/Definition of Done je Paket:**
- P0: BSL-Block live, /baselines, RLD-Boot, two-levels-red Logging
- P1: Heat-FSM, Multipliers sichtbar/stabil, 5 Events liefern Text, /heat ok
- P2: FFT-Peaks, Rampen stabil, Backstop greift, /spec & /backstop ok
- P3: Artifacts persistiert, EN-Parallel aktiv, Registry 3.5, CI grün, Audit-Extras
**Anbindung/Bestandsartefakte:**
- Keine Änderungen an Index & Loader, Scorefenster/Decay kompatibel zu SCR_TEMPLATE/SCH_TEMPLATE, Multipliers wirken als Vorfaktor. Baseline beeinflusst nur Kalibrierung, nicht Interpretation.
- Lizenz bleibt CC BY-NC-SA 4.0
**Tests & Qualität:**
- Unit: BaselineStore, Features, FSM-Transitions, FFT-Peaks, Ramp-Caps, Backstop
- E2E: Golden-Chats (verschiedene Gesprächsszenarien)
- CI-Gates: Priors-Datei valid, Normierung, support_k ≥3, Artifacts PII-minimal, Auditpflichfelder; keine Schemaänderungen erforderlich zur Migration von 3.4 → 3.5.
*Weitere Kontextvorgaben gemäß Originalspezifikation (PROMATRA_INSYS) und LD-3.4 Vorgaben sind als Rahmen weiterhin verbindlich. Implementierung erfolgt nach oben beschriebenem Upgradepfad. Remote-GUI/API bleibt generalisiert einsetzbar, keine localhost-Beschränkung, CORS via ENV.*
*ChatGPT kann Fehler machen. OpenAI verwendet keine Daten aus dem Arbeitsbereich DIYrigent GmbH zum Trainieren seiner Modelle.*
Request changes (optional)
