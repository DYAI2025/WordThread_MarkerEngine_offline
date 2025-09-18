# Iterativer Entwicklungsplan: Upgrade auf Lean-Deep 3.5 (LD3.5)

## Überblick

Dieser iterative Plan basiert auf der Spezifikation in `Specs_LD3.5.md` und folgt einem agilen Ansatz mit kurzen Iterationen (2-4 Wochen), um Risiken zu minimieren, Feedback zu integrieren und die Schema-Kompatibilität zu 3.4 zu wahren. Der Plan ist in Phasen unterteilt (P0-P3), mit Iterationen innerhalb jeder Phase. Jede Iteration endet mit Tests, Reviews und potenziellen Anpassungen. Gesamtdauer: Ca. 12-16 Wochen, abhängig von Teamgröße und Feedback.

### Grundprinzipien

-   **Priorisierung**: P0 zuerst (Must-Have), dann P1-P3.
-   **Iterationen**: 2-4 Wochen; Ende mit Demo, Tests und Akzeptanzprüfung.
-   **Risikomanagement**: Frühzeitige Prototypen für Baseline und FSM; Fallback zu 3.4 bei kritischen Problemen.
-   **Abhängigkeiten**: Baseline vor Heat-FSM; API-Endpunkte nach Modulen.
-   **Qualität**: Unit-Tests pro Modul; E2E-Tests pro Phase; CI-Gates aktiv.
-   **Team**: Annahme: 2-3 Entwickler (Backend, ML, DevOps); tägliche Stand-ups.

## Phase 1: P0 – Must-Have (Kernfunktionalität) – Dauer: 4-6 Wochen

**Ziel**: Basis-Implementierung mit Baseline-Schicht, API /baselines und Boot-Phase. Akzeptanz: BSL-Block live, /baselines funktional, RLD-Boot korrekt, two-levels-red Logging.

### Iteration 1.1: Baseline-Schicht Setup (2 Wochen)

-   **Aufgaben**:
    -   Erstelle `config/baselines.json` mit Priors, Gating-Optionen, Ramp, Multiplier.
    -   Implementiere `engine/baselines/store.py`: Klasse für BSL-Block-Speicher (pro Turn).
    -   Implementiere `engine/baselines/features.py`: 8 Features (TTB, RLD, YIR, IQP, NMD, ARP, IAD, CONG) pro 100T, DE+EN.
    -   Erstelle `engine/pipeline/hook_baselines.py`: Hook zwischen SEM und CLU.
    -   Unit-Tests: BaselineStore, Features.
-   **Risiken**: Inkompatibilität mit bestehender Pipeline; frühzeitig testen.
-   **Meilenstein**: Baseline-Features laufen in Testumgebung; Gating funktional.

### Iteration 1.2: API und Boot-Phase (2-3 Wochen)

-   **Aufgaben**:
    -   Erweitere `api_service.py`: Neuer Endpunkt `/baselines` (Read-only, JSON-Response mit letztem BSL-Block).
    -   Implementiere Domänen-Priorisierung (Therapy → Informal → Leadership → Support) in `config/baselines.json`.
    -   Boot-Phase: RLD nicht in T1/T2; IQP v2 mit kombinierter Triggerlogik.
    -   Logging: Two-levels-red (Micro/Domain-Abweichungen) in `engine_digest.py` integrieren.
    -   E2E-Tests: Golden-Chats für Baseline-Output.
-   **Risiken**: API-Performance; CORS/ENV-Konfiguration testen.
-   **Meilenstein**: /baselines liefert korrekte Daten; Boot-Phase stabil; Logging aktiv.

## Phase 2: P1 – Strong-Value (Erweiterte Funktionalität) – Dauer: 4-6 Wochen

**Ziel**: Heat-FSM, Events, Multipliers und /heat. Akzeptanz: FSM stabil, Multipliers sichtbar, 5 Events mit Text, /heat ok.

### Iteration 2.1: Heat-FSM und Events (2 Wochen)

-   **Aufgaben**:
    -   Implementiere `engine/runtime/heat_fsm.py`: Zustände (STABLE/WARMING/HOT/COOLDOWN); kein HOT in Boot.
    -   Implementiere `engine/runtime/events.py`: 5 Runtime-Events (silent_spike, question_overhang, imperative_burst, congruence_break, withdrawal) mit Textvorschlägen.
    -   Integriere in Pipeline: FSM nach Baseline-Hook.
    -   Unit-Tests: FSM-Transitions, Events.
-   **Risiken**: FSM-Zustandsübergänge; testen mit simulierten Turns.
-   **Meilenstein**: FSM wechselt Zustände korrekt; Events triggern mit Text.

### Iteration 2.2: Multipliers und API (2-3 Wochen)

-   **Aufgaben**:
    -   Implementiere `engine/runtime/multiplier_policy.py`: TTL-Multipliers (familienbasiert, capped).
    -   Erweitere `api_service.py`: Endpunkt `/heat` (sichtbar, JSON mit FSM-Zustand).
    -   Scores normiert halten; Multipliers als Vorfaktor in `scoring_engine.py`.
    -   E2E-Tests: Multipliers in Golden-Chats; /heat funktional.
-   **Risiken**: Score-Verzerrungen; Validierung mit Decay.
-   **Meilenstein**: Multipliers TTL-stabil und sichtbar; /heat ok.

## Phase 3: P2 – Stabilität/Frühwarnung (Monitoring) – Dauer: 2-4 Wochen

**Ziel**: FFT, Ramp-Guard, Backstop. Akzeptanz: FFT-Peaks erkannt, Rampen stabil, Backstop greift, /spec & /backstop ok.

### Iteration 3.1: FFT und Ramp-Guard (2 Wochen)

-   **Aufgaben**:
    -   Implementiere `engine/baselines/fft.py`: FFT auf CONG/IAD/RLD (6-8 Turns, Peaks 2–6 Taktungen).
    -   Implementiere `engine/runtime/ramp_guard.py`: Ramp-Guard + MEF + Stop-Delay.
    -   Unit-Tests: FFT-Peaks, Ramp-Caps.
-   **Risiken**: FFT-Performance; testen mit historischen Daten.
-   **Meilenstein**: Peaks erkannt; Rampen stabil.

### Iteration 3.2: Backstop und Audit (1-2 Wochen)

-   **Aufgaben**:
    -   Implementiere `engine/monitor/backstop.py`: Backstop (3 Levels) + Evidence-Buffer in `engine/actions/buffer.py`.
    -   Erweitere `api_service.py`: Endpunkte `/spec` und `/backstop` für Audit.
    -   E2E-Tests: Backstop greift; Audit-Endpunkte liefern Daten.
-   **Risiken**: Buffer-Overflow; Monitoring-Tools integrieren.
-   **Meilenstein**: Backstop aktiv; /spec & /backstop ok.

## Phase 4: P3 – Ops & Compliance (Betrieb) – Dauer: 2-4 Wochen

**Ziel**: Artifacts, Lexika, Registry, Docs. Akzeptanz: Artifacts persistiert, EN-Parallel aktiv, Registry 3.5, CI grün.

### Iteration 4.1: Artifacts und Lexika (2 Wochen)

-   **Aufgaben**:
    -   Implementiere `/artifacts/{hash}` in `api_service.py`: PII-minimal Snapshots, 30 Tage Retention.
    -   DE/EN-Lexika für Pronomen/Negation; Language-Auto-Detect in `numeric_normalizer_plugin.py`.
    -   CI-Gates: Priors-Datei valid, p/100T Normierung, support_k ≥3.
-   **Risiken**: PII-Verstöße; Audit-Pflichtfelder prüfen.
-   **Meilenstein**: Artifacts persistiert; EN-Parallel aktiv.

### Iteration 4.2: Registry und Docs (1-2 Wochen)

-   **Aufgaben**:
    -   Aktualisiere `DETECT_registry.json` auf 3.5; neue Klassen eintragen.
    -   Aktualisiere CHANGELOG.md und README.md.
    -   Vollständige CI-Gates; keine Schemaänderungen.
-   **Risiken**: Dokumentationslücken; Review mit Stakeholdern.
-   **Meilenstein**: Registry 3.5; CI grün; Docs vollständig.

## Integration des neuen Arbeitsauftrags: Vorbereitungsentwicklungsdatei

Basierend auf der bereitgestellten "Vorbereitungsentwicklungsdatei" habe ich den iterativen Plan erweitert. Dieser Arbeitsauftrag definiert detaillierte Must-Haves (A-H), Sprints (1-7), Schnittstellen, Risiken und Dokumentation. Der Plan wird angepasst, um diese Prioritäten zu integrieren, wobei die Sprints als neue Phasen dienen. Gesamtdauer: Ca. 14-18 Wochen (7 Sprints à 2 Wochen).

### Aktualisierte Grundprinzipien

-   **Priorisierung**: Must-Haves A-H zuerst (blockierend), dann Nice-to-Haves.
-   **Iterationen**: 7 Sprints (2 Wochen pro Sprint); Ende mit Deliverables und Akzeptanz.
-   **Risikomanagement**: Gegenmaßnahmen aus Arbeitsauftrag (z.B. Migration auf Normalform, harte Pins).
-   **Abhängigkeiten**: Preflight vor Detection; Baselines vor Heat-FSM.
-   **Qualität**: Determinismus-Tests, Golden-Suites, Property-Tests.
-   **Team**: 2-3 Entwickler; tägliche Stand-ups.

### Neue Phasen basierend auf Sprints (Must-Haves A-H)

#### Sprint 1: Blocker entfernen (A1, A2, B1, B2) – Dauer: 2 Wochen

**Ziel**: Deterministische Detection + Windowing, Digest, Preflight grün.

-   **Aufgaben**:
    -   A1: Preflight-Resolver reparieren (validiert composed_of, Registry; bricht bei Fehlern ab).
    -   A2: Reproduzierbare Builds (requirements.txt mit ==, Lockfile; engine_digest implementieren).
    -   B1: Deterministische Detektor-Pipeline (Registry als { "detectors": [...] }, priority/id fix; Plugins integriert).
    -   B2: Conversation-Windowing (size/overlap, zeit-/indexstabil; msg_id, span, source).
-   **Risiken**: Registry-Mismatches; Gegenmaßnahme: Prosodie-Detektoren entfernen.
-   **Meilenstein**: 0 Missing-Refs; identische Runs; Snapshot-Tests grün.

#### Sprint 2: Komposition vervollständigen (C1, C2) – Dauer: 2 Wochen

**Ziel**: Vollständige Activation-Engine, Evidenzkaskaden, Golden-Tests.

-   **Aufgaben**:
    -   C1: Activation-Normalform (alle Marker nutzen activation: { rule, params }; Migrationsskript für Freitext).
    -   C2: Regel-Engine (ANY, ALL, X_OF_Y, AT_LEAST_DISTINCT, FREQUENCY, WEIGHTED_AND; fensterbezogen).
-   **Risiken**: Regel-Ambiguität; Gegenmaßnahme: Migration vor Komposition.
-   **Meilenstein**: 0 Freitext-Regeln; 12 Golden-Tests grün; Evidenzkaskade vollständig.

#### Sprint 3: LD-3.5 Baselines & Heat (D1, D2, E1, E2) – Dauer: 2 Wochen

**Ziel**: Baselines + FSM mit Endpunkten und Multipliers.

-   **Aufgaben**:
    -   D1: Baselines berechnen (TTB, RLD, IAD, YIR; Schnittstelle { "window_idx": 12, "features": {...} }).
    -   D2: Baseline-Gating/Weighting (Schwellen/Multipliers deterministisch).
    -   E1: FSM implementieren (STABLE/WARMING/HOT/COOLDOWN; Ramp-Sperre).
    -   E2: Events & Multipliers (FSM-Events; Multipliers im Scoring).
-   **Risiken**: Nicht-Determinismus; Gegenmaßnahme: Engine-Digest, Property-Tests.
-   **Meilenstein**: /baselines und /heat liefern erwartete Werte; Ramp-Guard aktiv.

#### Sprint 4: Intuition v3.3 final (F1, F2) – Dauer: 2 Wochen

**Ziel**: Intuition-Hook, Guardian/EWMA/Telemetry, Multipliers im Scoring.

-   **Aufgaben**:
    -   F1: Runtime-Hook contextual*rescan (Guardian-Policy, EWMA-Präzision, CLU_INTUITION*\*-Hits).
    -   F2: Multipliers im Scoring (Confirmed/Decayed steuern Multipliers; YAML unverändert).
-   **Risiken**: Leistung; Gegenmaßnahme: Profiling, O(n)-Fensteraggregate.
-   **Meilenstein**: /telemetry/intuition korrekt; Multipliers nur im Scoring.

#### Sprint 5: Scoring & Drift (G1, G2) – Dauer: 2 Wochen

**Ziel**: Stabile Scores, Trends, Drift-Events.

-   **Aufgaben**:
    -   G1: Scoring-Pipeline (base/weight/logistic/decay → Schema-Fusion → Aggregates/Trends).
    -   G2: Drift-Achsen (Loader liest Definitionen; Events erzeugen).
-   **Risiken**: Drift/Nicht-Determinismus; Gegenmaßnahme: Harte Pins.
-   **Meilenstein**: /scores und /drift deterministisch; Mind. 3 Achsen aktiv.

#### Sprint 6: API & Artefakte (H1, H2) – Dauer: 2 Wochen

**Ziel**: Vollständige HTTP-Schicht, write-once Artefakte, OpenAPI.

-   **Aufgaben**:
    -   H1: HTTP-API neu (POST /analyze, GET /baselines, /heat, /scores, /drift, /telemetry/intuition, /health, /artifacts/{hash}).
    -   H2: Artefakt-Persistenz & Digest (Write-once mit Input-Hash und Engine-Digest).
-   **Risiken**: API-Performance; Gegenmaßnahme: Batch-Regex.
-   **Meilenstein**: OpenAPI validiert; Responses gegen Schemata; Artefakte write-once.

#### Sprint 7: Stabilisierung – Dauer: 2 Wochen

**Ziel**: CI-Erweiterungen, Performance-Profiling, Doku.

-   **Aufgaben**:
    -   CI-Erweiterungen (Golden-Suites, Property-Tests, Linter/Formatter/Mypy).
    -   Performance-Profiling (Latenz, Throughput).
    -   Dokumentation erstellen/aktualisieren (ENGINE_OVERVIEW.md, RUNTIME_GUIDE.md, SCHEMA_REFERENCE.md, INTUITION_GUIDE.md, BASELINES_HEAT.md, CONTRIBUTING.md).
-   **Risiken**: Dokumentationslücken; Gegenmaßnahme: Review mit Stakeholdern.
-   **Meilenstein**: CI grün; Docs vollständig; Repo 100% LD-3.5-ready.

### Nice-to-Haves (nach Sprint 7)

-   Optionale Baseline-Features (CONG, IAR, VOL, SCL).
-   Erweitertes Drift-Dashboard.
-   Profile/Archetypen-Layer.
-   CLI-Tooling (ld35 run, diff, explain).
-   Konfig-Hot-Reload.
-   Prometheus-Metrics.

### Schnittstellen und Abnahmekriterien

-   **Inputformat**: Wie definiert (conversation_id, messages, precomputed_ato_events, meta).
-   **Determinismus**: Drei identische Läufe → identisches Artefakt + Digest.
-   **Definition of Done**: Alle Must-Haves erfüllt; CI grün; Artefakte write-once.

### Risiken & Gegenmaßnahmen (aus Arbeitsauftrag)

-   Regel-Ambiguität → Migration auf Normalform.
-   Drift/Nicht-Determinismus → Harte Pins, Engine-Digest.
-   Registry-Mismatches → Prosodie als externe ATO-Events.
-   Leistung → Profiling, O(n)-Aggregate.

Dieser erweiterte Plan integriert den Arbeitsauftrag vollständig. Starte mit Sprint 1 für Blocker-Entfernung.
