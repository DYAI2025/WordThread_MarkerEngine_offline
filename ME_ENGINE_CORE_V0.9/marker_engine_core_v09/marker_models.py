
from dataclasses import dataclass
from enum import Enum

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
class MarkerMatch:
    chunk_id: str
    marker_id: str
    marker_name: str
    category: MarkerCategory
    severity: MarkerSeverity
    confidence: float
    metadata: dict
