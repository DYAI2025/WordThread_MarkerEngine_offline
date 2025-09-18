Spezifikation der Anforderungen: Erweiterter Dev-Auftrag – Upgrade auf Lean-Deep 3.5 (LD3.5 Up.md)
Basierend auf der bereitgestellten Datei eRWEITERTER DEV-AUFTRAG –LD3.5 Up.md habe ich die Anforderungen analysiert und in eine strukturierte, formale Spezifikation umgewandelt. Diese Spezifikation bricht die Inhalte in klare Kategorien auf, um die technischen, funktionalen und qualitativen Anforderungen zu definieren. Ich habe dabei auf Vollständigkeit, Konsistenz und Machbarkeit geachtet. Die Spezifikation ist schema-kompatibel zu LD 3.4 und fokussiert auf Runtime-Änderungen ohne Marker-Schema-Modifikationen.

1. Überblick und Ziele
   Primäres Ziel: Migration der Transcriber-Lösung (TWE Core) auf Lean-Deep 3.5. Dies umfasst eine schema-kompatible Erweiterung ohne Änderungen am bestehenden Marker-Schema. Upgrades beschränken sich auf Engine-Logik, Detektoren, Konfiguration (inkl. Domänen-Priorisierung: Therapy → Informal → Leadership → Support) und API-Endpunkte.
   Qualitätskriterium: Lauffähige Runtime-Funktion mit sichtbar verwertbarem Output. Keine localhost-Beschränkungen; Remote-GUI/API generalisiert einsetzbar mit CORS via ENV.
   Sprachunterstützung: Parallel DE+EN; alle IDs, Dateien und Marker-Namen auf Englisch.
   Kompatibilität: Vier-Ebenen-Architektur (ATO → SEM → CLU → MEMA) und Intuitionslogik (CLU-basiert) bleiben unverändert. Marker-YAMLs und Mongo-Collections (Definitions- und Runtime-Events) unverändert. Scoring-Fenster und Aggregation mit Decay bleiben kompatibel; Multipliers und Rampen-Wächter als Ergänzungen.
   Lizenz: CC BY-NC-SA 4.0 bleibt bestehen.
2. Architektonische Änderungen
   Neue Pipeline: Messages → ATO → SEM → [NEU: Baseline-Hook] → CLU → MEMA.
   Neue Runtime-Module (zwischen SEM und CLU):
   Baseline-Schicht: 8 Features (TTB, RLD, YIR, IQP, NMD, ARP, IAD, CONG) pro 100T, DE+EN.
   Heat-FSM: Zustände (STABLE/WARMING/HOT/COOLDOWN).
   TTL-Multipliers: Familienbasiert, capped.
   Frequency-Layer: FFT auf CONG/IAD/RLD, 6-8 Turns.
   Ramp-Guard + MEF + Stop-Delay.
   Backstop + Evidence-Buffer.
   Intuitionslogik: Bleibt CLU-basiert; Baselines ergänzen, nicht ersetzen.
3. Funktionale Anforderungen (Priorisiert nach P0-P3)
   P0 – Must-Have (Kernfunktionalität):
   Baseline-Schicht/Features implementieren mit Gating.
   API-Endpunkt /baselines (Read-only): Liefert letzten BSL-Block pro Turn.
   Domänen-Priorisierung (Therapy → Informal → Leadership → Support) mit spezifischen Heuristiken (Priors).
   Boot-Phase: RLD greift nicht in T1/T2; IQP v2 mit kombinierter Triggerlogik.
   Logging: Two-levels-red (Abweichungen auf Micro- und Domain-Ebene).
   P1 – Strong-Value (Erweiterte Funktionalität):
   Heat-FSM: Zustandsbasiert, stabil reproduzierbar, kein HOT in Boot-Phase.
   5 Runtime-Events (silent_spike, question_overhang, imperative_burst, congruence_break, withdrawal): Mit Textvorschlägen im Analyseoutput.
   Multipliers: TTL-stabil, sichtbar; Scores normiert und stabil.
   API-Endpunkt /heat: Sichtbar und funktional.
   P2 – Stabilität/Frühwarnung (Monitoring und Sicherheit):
   FFT für CONG/IAD/RLD: Peaks erkennen (2–6 Taktungen).
   Rampen-Wächter, Stop-Delay, Backstop (3 Levels).
   Audit-Endpunkte: /spec und /backstop für Zeit/Frequenz-Analyse.
   P3 – Ops & Compliance (Betrieb und Dokumentation):
   Telemetry-Artifacts: Via /artifacts/{hash}, PII-minimal, 30 Tage Retention.
   DE/EN-Lexika: Für Pronomen/Negation, Language-Auto-Detect.
   Registry-Erweiterung: DETECT_registry.json auf Version 3.5, neue Klassen eintragen.
   Dokumentation: CHANGELOG und README aktualisieren.
   CI/Gate: Priors-Datei valid, p/100T Normierung, support_k ≥3.
4. Artefakte und Schnittstellen
   Konfiguration:
   config/baselines.json: Inkl. Priors, Gating-Optionen, Ramp, Multiplier.
   Neue/Erweiterte Module:
   engine/baselines/store.py
   engine/baselines/features.py
   engine/pipeline/hook_baselines.py
   engine/runtime/heat_fsm.py
   engine/runtime/events.py
   engine/runtime/multiplier_policy.py
   engine/baselines/fft.py
   engine/runtime/ramp_guard.py
   engine/monitor/backstop.py
   engine/actions/buffer.py
   api_service.py: Neue Endpunkte integrieren.
   Bestandsartefakte: Keine Änderungen an Index, Loader, SCR_TEMPLATE, SCH_TEMPLATE. Multipliers als Vorfaktor; Baseline beeinflusst nur Kalibrierung.
5. Akzeptanzkriterien (Definition of Done)
   P0: BSL-Block live, /baselines funktional, RLD-Boot korrekt, two-levels-red Logging aktiv.
   P1: Heat-FSM stabil, Multipliers sichtbar/stabil, 5 Events mit Text, /heat ok.
   P2: FFT-Peaks erkannt, Rampen stabil, Backstop greift, /spec & /backstop ok.
   P3: Artifacts persistiert, EN-Parallel aktiv, Registry 3.5, CI grün, Audit-Extras implementiert.
6. Tests und Qualitätssicherung
   Unit-Tests: BaselineStore, Features, FSM-Transitions, FFT-Peaks, Ramp-Caps, Backstop.
   E2E-Tests: Golden-Chats (verschiedene Gesprächsszenarien).
   CI-Gates: Priors-Datei valid, Normierung, support_k ≥3, Artifacts PII-minimal, Audit-Pflichtfelder; keine Schemaänderungen für Migration 3.4 → 3.5.
   Artifacts: PII-minimal Telemetry-Snapshots, 30 Tage Retention.
7. Risiken und Annahmen
   Risiken: Potenzielle Inkompatibilitäten bei Runtime-Modulen; Abhängigkeit von bestehenden Loadern und Collections.
   Annahmen: Originalspezifikation (PROMATRA_INSYS) und LD-3.4 Vorgaben bleiben Rahmen. Keine Daten aus DIYrigent GmbH werden für Training verwendet (OpenAI Disclaimer).
   Fallback: Bei Problemen: Schema-kompatibilität priorisieren; ggf. Rollback zu 3.4.
   Diese Spezifikation ist vollständig und direkt aus der Datei abgeleitet. Falls du spezifische Aspekte (z.B. technische Details zu einem Modul) vertiefen möchtest oder Probleme in der Implementierung identifiziert hast, lass es mich wissen – ich kann dann Tools nutzen, um den Code zu analysieren oder Fixes vorzuschlage
