
from scoring_engine import ScoringEngine
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

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

def to_matches(hits, messages):
    mm = []
    for h in hits:
        # Find the message id for the hit. This is a placeholder
        # and should be improved to correctly associate hits with messages.
        msg_id = messages[0]["id"]
        meta = h.get("meta", {})
        mm.append(MarkerMatch(
            chunk_id=msg_id,
            marker_id=h["marker"],
            marker_name=h.get("name", h["marker"]),
            category=MarkerCategory[meta.get("category","POSITIVE")],
            severity=MarkerSeverity[meta.get("severity","LOW")],
            confidence=float(meta.get("confidence", 0.8)),
            metadata={"weight": meta.get("weight", 1.0)}
        ))
    return mm

def run_scoring(messages, engine_output):
    se = ScoringEngine()
    chunks = to_chunks(messages)
    matches = to_matches(engine_output["hits"], messages)
    return se.calculate_scores(chunks, matches)
