"""
drift_axes.py
Implements drift axes mapping and event emission for aggregated scores.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DriftEvent:
    axis_id: str
    axis_name: str
    value: float
    threshold: float
    direction: str  # "above" or "below"
    timestamp: datetime
    metadata: Dict[str, Any]

class DriftAxesManager:
    """Manages drift axes definitions and event emission."""

    def __init__(self, drift_axes_path: str = "drift_axes.zip"):
        self.axes_definitions = {}
        self.active_events = []
        self._load_drift_axes(drift_axes_path)

    def _load_drift_axes(self, path: str):
        """Load drift axes definitions from file."""
        # Placeholder for loading drift axes definitions
        # In a real implementation, this would load from drift_axes.zip
        self.axes_definitions = {
            "relationship_health_drift": {
                "name": "Relationship Health Drift",
                "description": "Tracks changes in relationship health over time",
                "thresholds": {
                    "critical_low": 2.0,
                    "warning_low": 3.5,
                    "normal": 5.0,
                    "warning_high": 6.5,
                    "critical_high": 8.0
                },
                "score_mappings": {
                    "relationship_health": 1.0,
                    "manipulation_index": -0.5,
                    "communication_quality": 0.8
                }
            },
            "manipulation_risk_drift": {
                "name": "Manipulation Risk Drift",
                "description": "Monitors increasing manipulation patterns",
                "thresholds": {
                    "critical": 7.0,
                    "warning": 5.0,
                    "normal": 3.0
                },
                "score_mappings": {
                    "manipulation_index": 1.0,
                    "gaslighting": 1.5,
                    "fraud_probability": 1.2
                }
            },
            "emotional_dysregulation_drift": {
                "name": "Emotional Dysregulation Drift",
                "description": "Tracks emotional stability patterns",
                "thresholds": {
                    "critical": 6.0,
                    "warning": 4.0,
                    "normal": 2.0
                },
                "score_mappings": {
                    "emotional_abuse": 1.0,
                    "love_bombing": 0.8,
                    "boundary_violation": 0.6
                }
            }
        }

    def calculate_drift_values(self, aggregated_scores: Dict[str, Any]) -> Dict[str, float]:
        """Calculate drift values for each axis based on aggregated scores."""
        drift_values = {}

        for axis_id, axis_def in self.axes_definitions.items():
            drift_value = 0.0
            score_mappings = axis_def.get("score_mappings", {})

            for score_type, weight in score_mappings.items():
                if score_type in aggregated_scores:
                    score_obj = aggregated_scores[score_type]
                    # Extract the average score from AggregatedScore object
                    if hasattr(score_obj, 'average_score'):
                        score_value = score_obj.average_score
                    else:
                        score_value = float(score_obj)
                    drift_value += score_value * weight

            drift_values[axis_id] = drift_value

        return drift_values

    def check_thresholds(self, drift_values: Dict[str, float]) -> List[DriftEvent]:
        """Check drift values against thresholds and emit events."""
        events = []

        for axis_id, value in drift_values.items():
            axis_def = self.axes_definitions.get(axis_id, {})
            thresholds = axis_def.get("thresholds", {})

            # Check critical thresholds
            if "critical" in thresholds:
                if value >= thresholds["critical"]:
                    events.append(DriftEvent(
                        axis_id=axis_id,
                        axis_name=axis_def.get("name", axis_id),
                        value=value,
                        threshold=thresholds["critical"],
                        direction="above",
                        timestamp=datetime.utcnow(),
                        metadata={"level": "critical"}
                    ))
            elif "critical_high" in thresholds and value >= thresholds["critical_high"]:
                events.append(DriftEvent(
                    axis_id=axis_id,
                    axis_name=axis_def.get("name", axis_id),
                    value=value,
                    threshold=thresholds["critical_high"],
                    direction="above",
                    timestamp=datetime.utcnow(),
                    metadata={"level": "critical_high"}
                ))
            elif "critical_low" in thresholds and value <= thresholds["critical_low"]:
                events.append(DriftEvent(
                    axis_id=axis_id,
                    axis_name=axis_def.get("name", axis_id),
                    value=value,
                    threshold=thresholds["critical_low"],
                    direction="below",
                    timestamp=datetime.utcnow(),
                    metadata={"level": "critical_low"}
                ))

            # Check warning thresholds
            if "warning" in thresholds:
                if value >= thresholds["warning"]:
                    events.append(DriftEvent(
                        axis_id=axis_id,
                        axis_name=axis_def.get("name", axis_id),
                        value=value,
                        threshold=thresholds["warning"],
                        direction="above",
                        timestamp=datetime.utcnow(),
                        metadata={"level": "warning"}
                    ))
            elif "warning_high" in thresholds and value >= thresholds["warning_high"]:
                events.append(DriftEvent(
                    axis_id=axis_id,
                    axis_name=axis_def.get("name", axis_id),
                    value=value,
                    threshold=thresholds["warning_high"],
                    direction="above",
                    timestamp=datetime.utcnow(),
                    metadata={"level": "warning_high"}
                ))
            elif "warning_low" in thresholds and value <= thresholds["warning_low"]:
                events.append(DriftEvent(
                    axis_id=axis_id,
                    axis_name=axis_def.get("name", axis_id),
                    value=value,
                    threshold=thresholds["warning_low"],
                    direction="below",
                    timestamp=datetime.utcnow(),
                    metadata={"level": "warning_low"}
                ))

        self.active_events.extend(events)
        return events

    def get_active_events(self) -> List[DriftEvent]:
        """Get currently active drift events."""
        return self.active_events.copy()

    def clear_events(self):
        """Clear all active events."""
        self.active_events.clear()
