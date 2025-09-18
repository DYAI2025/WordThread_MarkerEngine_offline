# =====================================================================
# SCR_score_models.py   –   Lean-Deep 3.2 Datenmodelle (vollständig)
# =====================================================================
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

# Adjust the import below if the relative import fails; use absolute import as fallback:
try:
    from ..matcher.marker_models import MarkerCategory, MarkerSeverity
except ImportError:
    from matcher.marker_models import MarkerCategory, MarkerSeverity

class ScoreType(str, Enum):
    """Verschiedene Score-Typen für die Analysen."""
    MANIPULATION_INDEX   = "manipulation_index"
    RELATIONSHIP_HEALTH  = "relationship_health"
    FRAUD_PROBABILITY    = "fraud_probability"
    EMOTIONAL_SUPPORT    = "emotional_support"
    CONFLICT_LEVEL       = "conflict_level"
    COMMUNICATION_QUALITY= "communication_quality"
    TRUST_LEVEL          = "trust_level"
    RESOURCE_BALANCE     = "resource_balance"
    RISK_SCORE           = "risk_score"                  # 3.2-neu

class ScoringModel(BaseModel):
    """Definition eines Scoring-Modells · Lean-Deep 3.2"""
    schema_version: str = Field("3.2", const=True)
    id: str = Field(..., description="Eindeutige Model-ID")
    name: str = Field(..., description="Name des Modells")
    type: ScoreType = Field(..., description="Score-Typ")
    description: str

    category_weights: Dict[MarkerCategory, float] = Field(default_factory=dict)
    severity_multipliers: Dict[MarkerSeverity, float] = Field(
        default_factory=lambda: {
            MarkerSeverity.LOW: 0.5,
            MarkerSeverity.MEDIUM: 1.0,
            MarkerSeverity.HIGH: 2.0,
            MarkerSeverity.CRITICAL: 3.0
        }
    )

    scale_min: float = 0.0                 # 3.2 – erlaubt 0-10
    scale_max: float = 10.0
    inverse_scale: bool = False
    normalization_factor: float = 100.0

    thresholds: Dict[str, float] = Field(
        default_factory=lambda:{
            "critical": 8.0,
            "warning" : 6.0,
            "normal"  : 4.0,
            "good"    : 2.0
        }
    )
    active: bool = True
