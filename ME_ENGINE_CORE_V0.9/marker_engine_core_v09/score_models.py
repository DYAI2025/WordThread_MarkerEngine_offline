from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from marker_models import MarkerCategory, MarkerSeverity

class ScoreType(Enum):
    MANIPULATION_INDEX = "manipulation_index"
    RELATIONSHIP_HEALTH = "relationship_health"
    FRAUD_PROBABILITY = "fraud_probability"
    COMMUNICATION_QUALITY = "communication_quality"

@dataclass
class ScoringModel:
    id: str
    name: str
    type: ScoreType
    description: str
    category_weights: Dict[MarkerCategory, float]
    inverse_scale: bool = False
    thresholds: Optional[Dict[str, float]] = None
    severity_multipliers: Optional[Dict[MarkerSeverity, float]] = None
    normalization_factor: float = 1.0
    scale_min: float = 1.0
    scale_max: float = 10.0
    active: bool = True

@dataclass
class ChunkScore:
    chunk_id: str
    model_id: str
    score_type: ScoreType
    raw_score: float
    normalized_score: float
    contributing_markers: List[Dict[str, Any]]
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AggregatedScore:
    model_id: str
    score_type: ScoreType
    average_score: float
    min_score: float
    max_score: float
    trend: str
    trend_strength: float
    chunk_count: int
    distribution: Dict[str, int]
    top_markers: List[Dict[str, Any]]

@dataclass
class ScoringResult:
    chunk_scores: Optional[List[ChunkScore]] = None
    aggregated_scores: Optional[Dict[str, AggregatedScore]] = None
    speaker_scores: Optional[Dict[str, Dict[str, AggregatedScore]]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    alerts: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0

    def __post_init__(self):
        if self.chunk_scores is None: self.chunk_scores = []
        if self.aggregated_scores is None: self.aggregated_scores = {}
        if self.speaker_scores is None: self.speaker_scores = {}
        if self.timeline is None: self.timeline = []
        if self.alerts is None: self.alerts = []
        if self.summary is None: self.summary = {}

@dataclass
class ScoreComparison:
    model_id: str
    score_type: ScoreType
    score1: float
    score2: float
    delta: float
    change: str
