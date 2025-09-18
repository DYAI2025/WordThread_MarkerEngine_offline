Zielarchitektur (Text-only) in 8 nüchternen Schritten

Preflight-Resolver

Lade alle Marker, normalisiere activation/activation_logic in eine Normalform.

Validiere composed_of vollständig, Fehlreferenzen sind „fatal“.

Validere Detector-Registry: jedes fires_marker muss existieren.

Ergebnis: engine_digest über Marker/Registry/Schemata/Code.

Normalisierung

Unicode NFKC, Leerzeichen-Policy, Emoji-Behandlung, Satzsegmentierung.

Numeric-Plugin ausführen, ATO_NUMERIC_ESTIMATE feuern und Payload als Evidenz sichern.

ATO-Detektion

Registry-Detektoren deterministisch (priority, id) abfahren.

Plugins (z. B. Numeric) ebenfalls als Detektoren behandeln. Evidenz: Spans, Source, Payload.

SEM/CLU/MEMA-Komposition

Fensterbasiert über Konversations-Chunks: size=30, overlap=0 oder wie in euren SCR-Schemata.

activation auswerten: ALL, ANY k, WEIGHTED_AND, X_OF_Y.

Evidenz-Kaskade beibehalten: welche ATO/SEM hat wen aktiviert, in welchen Nachrichten.

Scoring

Erst Marker-Score (base/weight/logistic/decay), dann Schema-Gewichte (Relation 3.4, Self-Deep etc.).

Danach in Scoring-Engine einspeisen: Adapter erzeugt TextChunk + MarkerMatch. Modelle berechnen Aggregates, Trends, Speaker-Splits, Alerts.

Drift-Achsen

Aggregierte Scores und Serien auf eure Drift-Achsen mappen. Grenzwerte aus drift_axes.zip anwenden, Events emittieren.

API und Artefakte

/analyze für Konversation → komplette Evidenz, Scores, Drift, Summaries, engine_digest.

/scores für reine Modell-Ergebnisse, /drift für Achsen/Events.

Run-Artefakte write-once speichern (Input-Hash, Engine-Digest, Ergebnisse).

Frontends

Das Modul ist headless. Web/CLI/Extension konsumieren nur die API. Voice bleibt upstream.

Konkrete Umsetzung: Code-Snippets und Adapter
A) Plugin-Integration in die Detektion

Hängt das Numeric-Payload an Treffer an und registriert das Plugin als Detector.

# detectors/plugin_numeric.py
from numeric_normalizer_plugin import NumericNormalizerPlugin

class NumericDetector:
    id = "plugin.numeric.normalizer"
    fires = ["ATO_NUMERIC_ESTIMATE"]

    def __init__(self):
        self.plugin = NumericNormalizerPlugin()

    def run(self, text):
        out = self.plugin.run(text)
        hits = []
        for m in out.get("fires", []):
            hits.append({
                "marker": m,
                "source": self.id,
                "payload": out.get("payload", {}),
                "evidence": {"span": out["payload"].get("original_text")}
            })
        return hits

B) Conversation-Pipeline (ersetzt PIPELINE.py)

Deine alte Demo analysiert jede Nachricht isoliert. Hier ist die deterministische Fenster-Variante mit Evidenz-Kaskade.

# CONV_PIPELINE.py
from datetime import datetime
from marker_engine_core import MarkerEngine

CHAT = [
    {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker":"A", "text":"Du bist süß ;)"},
    {"id": "m2", "ts": "2025-07-01T09:01:00", "speaker":"B", "text":"Nicht verraten!"},
    # ...
]

engine = MarkerEngine(config="config.ld34.json")  # lädt Marker/Registry/Schemata
result = engine.analyze_conversation(
    messages=CHAT,
    window={"size": 30, "overlap": 0},
    options={"locale":"de-DE","timezone":"Europe/Berlin"}
)

print(result["summary"])

C) Scoring-Adapter zu scoring_engine.py

Wir formen Engine-Treffer in TextChunk und MarkerMatch und lassen die Modelle laufen. Modelle, Trend, Alerts und Speaker-Aggregation kommen fertig aus der Engine.

# scoring_adapter.py
from scoring_engine import ScoringEngine  # nutzt eigene Modelle
from dataclasses import dataclass
from enum import Enum

# Minimale Kompatibilitäts-Modelle (falls eure Pakete fehlen)
class MarkerCategory(Enum):
    POSITIVE="POSITIVE"; EMPATHY="EMPATHY"; SUPPORT="SUPPORT"
    MANIPULATION="MANIPULATION"; GASLIGHTING="GASLIGHTING"
    EMOTIONAL_ABUSE="EMOTIONAL_ABUSE"; LOVE_BOMBING="LOVE_BOMBING"
    FRAUD="FRAUD"; FINANCIAL_ABUSE="FINANCIAL_ABUSE"
    CONFLICT_RESOLUTION="CONFLICT_RESOLUTION"; BOUNDARY_SETTING="BOUNDARY_SETTING"
    SELF_CARE="SELF_CARE"

class MarkerSeverity(Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"

@dataclass
class TextChunk:
    id: str
    text: str
    timestamp: datetime
    speaker: type("Speaker", (), {"name": str})  # quick shim
    word_count: int

@dataclass
class MarkerMatch:
    chunk_id: str
    marker_id: str
    marker_name: str
    category: MarkerCategory
    severity: MarkerSeverity
    confidence: float
    metadata: dict

def to_chunks(messages):
    chunks = []
    for i, m in enumerate(messages):
        chunks.append(TextChunk(
            id=m["id"], text=m["text"], timestamp=datetime.fromisoformat(m["ts"]),
            speaker=type("S", (), {"name": m.get("speaker","")}),
            word_count=len(m["text"].split())
        ))
    return chunks

def to_matches(hits):
    mm = []
    for h in hits:
        meta = h.get("meta", {})
        mm.append(MarkerMatch(
            chunk_id=h["msg_id"],
            marker_id=h["marker_id"],
            marker_name=h.get("name", h["marker_id"]),
            category=MarkerCategory[meta.get("category","POSITIVE")],
            severity=MarkerSeverity[meta.get("severity","LOW")],
            confidence=float(meta.get("confidence", 0.8)),
            metadata={"weight": meta.get("weight", 1.0)}
        ))
    return mm

def run_scoring(messages, engine_output):
    se = ScoringEngine()
    chunks = to_chunks(messages)
    matches = to_matches(engine_output["flattened_hits"])
    return se.calculate_scores(chunks, matches)

Agent-Auftrag: was exakt zu tun ist
Phase 0: Preflight und Hygiene

Resolver bauen:

Abgleichen aller composed_of-IDs, jeden Missing als Fehler reporten.

Alle Registry-fires_marker gegen Marker-Index prüfen.
Akzeptanz: CI schlägt fehl, wenn ≥1 Referenz fehlt. Report mit Liste und Pfaden.

Activation vereinheitlichen:

activation_logic in Normalform activation {rule, params} migrieren.
Akzeptanz: Linter bestätigt 0 Vorkommen von activation_logic.

Versionen pinnen:

requirements.txt auf == umstellen, Lockfile erzeugen, Engine-Digest implementieren.
Akzeptanz: gleicher Input → identischer Output-Hash in 3 Läufen.

Phase 1: Detection korrekt verdrahten

Plugin-Stage integrieren:

Numeric-Plugin als Detector registrieren, Payload in Evidenz.
Akzeptanz: Testfall „50k“ produziert ATO_NUMERIC_ESTIMATE mit normalized_numeric_value=50000.

Registry-Reihenfolge fixieren:

Sortierung (priority, id) erzwingen, Regex-Flags festlegen.
Akzeptanz: Snapshot-Test mit identischem Text ergibt identische Trefferreihenfolge.

Phase 2: Komposition & Fenster

Conversation-API implementieren:

analyze_conversation(messages, window, options) mit stabilen Fenstern.
Akzeptanz: Fenstergröße/Overlap reproducebar, Evidenz enthält Msg-IDs und Spans.

Activation-Engine:

Regeln ALL/ANY/WEIGHTED_AND/X_OF_Y implementieren, Thresholds testen.
Akzeptanz: 12 Goldens pro Regeltyp grün.

Phase 3: Scoring & Drift

Marker-Score + Schema-Gewichte:

Base/Weight/Logistic/Decay anwenden, dann Schema-Fusion.
Akzeptanz: Goldens zeigen identische End-Scores bei drei Wiederholungen.

Scoring-Adapter bauen:

Engine-Hits → TextChunk + MarkerMatch, dann ScoringEngine.calculate_scores.
Akzeptanz: Aggregates, Trends, Speaker-Scores und Alerts erscheinen.

Drift-Achsen anbinden:

Aggregierte Scores + Achsen-Definitionen verknüpfen, Events erzeugen.
Akzeptanz: Mindestens 3 Achsen mit Schwellenwerten liefern Events in Testläufen.

Phase 4: API + Artefakte

HTTP-Service (FastAPI/Flask):

/analyze, /scores, /drift, /health. Run-Artefakte write-once persistieren.
Akzeptanz: JSON validiert gegen eure 3.4-Schemata, engine_digest wird mitgeliefert.

CI & Tests:

Golden-Sätze pro Familie, Property-Tests (Shuffle-Invarianz), Snapshot-Timeline.
Akzeptanz: CI grün, 90%+ Branch Coverage auf Komposition/Scoring.

Kurz-Patch für die alte Demo-Pipeline

Eure jetzige Datei führt pro Nachricht engine.analyze(text) aus. Bitte ersetzen durch die Konversations-Variante oben; die alte Version ist nur als „Hello World“ brauchbar und ignoriert Windowing, Komposition und Evidenzketten.

Schnittstellen-Grenze zu Voice

Dieses Modul ist Text-only.

Voice/Prosodie liefert optional bereits berechnete ATO-Events als Input oder bleibt komplett getrennt.

Keine Abhängigkeit auf „PoseID“ oder Audio-Libs.

Falls Fusion nötig: nur über sauber definierte, versionierte ATO-Ereignisse injizieren, niemals Roh-Audio.

Was du am Ende bekommst

Deterministische Konversations-Analyse, die Marker-Evidenz, Komposition, Scoring, Trends, Alerts und Drift-Achsen sauber ausspielt.

Ein schnörkelloses HTTP-Modul, das sich problemlos vor jeden Frontend-Typ hängen lässt.

Keine Phantom-Treffer mehr, keine „mal so, mal so“ Scores