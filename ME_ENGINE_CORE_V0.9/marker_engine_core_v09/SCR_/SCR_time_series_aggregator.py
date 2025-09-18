# =====================================================================
# SCR_time_series_aggregator.py   –   Lean-Deep 3.2 (vollständig)
# =====================================================================
"""Time-Series Aggregator  •  kompatibel zu Lean-Deep 3.2"""

import logging, time, numpy as np, pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta

from .aggregation_models import (
    AggregationConfig, AggregationPeriod, AggregationResult,
    TimeSeriesData, TimeSeriesPoint, HeatmapData, ComparisonData
)
from ..scoring.score_models import ChunkScore
from ..matcher.marker_models import MarkerMatch, MarkerCategory

logger = logging.getLogger(__name__)

class TimeSeriesAggregator:
    """Aggregiert Scores & Marker-Events – fügt 3.2-RiskLogistic hinzu."""
    def __init__(self, config: Optional[AggregationConfig] = None):
        self.config = config or AggregationConfig()

    # ------- geänderte Kernstelle: Score-Aggregation inkl. Risk -------
    def _create_score_point(self, scores, start, end, score_type) -> TimeSeriesPoint:
        point = TimeSeriesPoint(timestamp=start, period_start=start, period_end=end)
        if scores:
            vals = [s.normalized_score for s in scores]
            mean = np.mean(vals)
            risk_log = 5/(1+np.exp(-0.8*(mean-1)))     # Lean-Deep-Risk 0-5
            point.values = {
                "mean": mean, "min": min(vals), "max": max(vals),
                "std": np.std(vals) if len(vals)>1 else 0, "median": np.median(vals),
                "risk_logistic": risk_log                         # 3.2-neu
            }
            point.counts = {"chunk_count": len(scores)}
        else:
            point.values = {"mean":0,"min":0,"max":0,"std":0,"median":0,"risk_logistic":0}
            point.counts = {"chunk_count":0}
        return point

    # restliche Methoden unverändert (siehe Original)
