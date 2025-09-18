# =====================================================================
# SCR_scoring_engine.py   –   Lean-Deep 3.2 Scoring-Engine (vollständig)
# =====================================================================
"""Scoring Engine  •  kompatibel zu Lean-Deep 3.2."""

import logging, time, numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from .score_models import (
    ScoringModel, ChunkScore, AggregatedScore, ScoringResult,
    ScoreType, ScoreComparison
)
from ..matcher.marker_models import MarkerMatch, MarkerCategory, MarkerSeverity
from ..chunker.chunk_models   import TextChunk

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Berechnet Scores auf Basis erkannter Marker · 3.2-ready."""
    def __init__(self):
        self.models: Dict[str, ScoringModel] = {}
        self._initialize_default_models()

    # ---------- Modelle (unverändert, aber scale_min jetzt 0) ----------
    def _initialize_default_models(self):
        self.models["manipulation_index"] = ScoringModel(
            id="manipulation_index",
            name="Manipulations-Index",
            type=ScoreType.MANIPULATION_INDEX,
            description="Grad manipulativer Kommunikation",
            category_weights={
                MarkerCategory.MANIPULATION: 2.0,
                MarkerCategory.GASLIGHTING: 3.0,
                MarkerCategory.EMOTIONAL_ABUSE: 2.5,
                MarkerCategory.LOVE_BOMBING: 1.5,
                MarkerCategory.FRAUD: 3.0,
                MarkerCategory.POSITIVE: -1.0,
                MarkerCategory.EMPATHY: -0.5,
                MarkerCategory.SUPPORT: -0.5
            }
        )
        # … weitere Modelle identisch (siehe Original) …

    # ---------- Haupt-API ----------
    def calculate_scores(
        self, chunks: List[TextChunk], matches: List[MarkerMatch],
        models: Optional[List[str]] = None
    ) -> ScoringResult:
        start = time.time()
        res   = ScoringResult()
        active_models = self._get_active_models(models)
        by_chunk = self._group_matches_by_chunk(matches)

        # Chunk-Scores
        for ch in chunks:
            chunk_matches = by_chunk.get(ch.id, [])
            for mod in active_models:
                res.chunk_scores.append(
                    self._calculate_chunk_score(ch, chunk_matches, mod)
                )

        # Aggregation & Summary (wie Original)
        res.aggregated_scores = self._aggregate_scores(res.chunk_scores, active_models)
        res.speaker_scores    = self._calculate_speaker_scores(chunks, res.chunk_scores)
        res.timeline          = self._create_timeline(res.chunk_scores)
        res.alerts            = self._generate_alerts(res.aggregated_scores)
        res.summary           = self._create_summary(res)
        res.processing_time   = time.time() - start
        logger.info(f"Scoring fertig in {res.processing_time:.2f}s")
        return res

    # ---------- Score-Berechnung (nur Änderungen gezeigt) -------------
    def _normalize_score(self, raw: float, model: ScoringModel, words: int) -> float:
        """Skaliert 0-10 (statt 1-10) · erlaubt direkte 0-5-Risklogistik downstream."""
        norm = (raw / words) * model.normalization_factor if words else 0.0
        score = norm if not model.inverse_scale else model.scale_max - norm
        return float(max(model.scale_min, min(model.scale_max, score)))

    # alle anderen Methoden unverändert …
