"""
test_complete_system.py
Comprehensive tests for the complete Marker Engine system.
"""

import unittest
from marker_engine_core import MarkerEngine
from scoring_adapter import run_scoring
from drift_axes import DriftAxesManager
import json

class TestCompleteSystem(unittest.TestCase):

    def setUp(self):
        self.engine = MarkerEngine()
        self.drift_manager = DriftAxesManager()

    def test_end_to_end_analysis(self):
        """Test complete analysis pipeline."""
        messages = [
            {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker": "A", "text": "Ich bin wütend"},
            {"id": "m2", "ts": "2025-07-01T09:01:00", "speaker": "B", "text": "Das tut mir leid"},
            {"id": "m3", "ts": "2025-07-01T09:02:00", "speaker": "A", "text": "Du bist süß ;)"},
        ]

        # Test conversation analysis
        result = self.engine.analyze_conversation(messages, {"size": 3, "overlap": 0}, {})

        # Verify hits are generated
        self.assertIsInstance(result["hits"], list)
        self.assertGreater(len(result["hits"]), 0)

        # Test scoring
        scoring_result = run_scoring(messages, result)

        # Verify scoring result structure
        self.assertIsInstance(scoring_result.aggregated_scores, dict)
        self.assertGreater(len(scoring_result.aggregated_scores), 0)

        # Test drift calculation
        aggregated_scores = scoring_result.aggregated_scores
        drift_values = self.drift_manager.calculate_drift_values(aggregated_scores)

        # Verify drift values
        self.assertIsInstance(drift_values, dict)
        self.assertGreater(len(drift_values), 0)

        # Test threshold checking
        events = self.drift_manager.check_thresholds(drift_values)
        self.assertIsInstance(events, list)

    def test_deterministic_output(self):
        """Test that same input produces same output."""
        messages = [
            {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker": "A", "text": "Test message"},
        ]

        # Run analysis multiple times
        results = []
        for _ in range(3):
            result = self.engine.analyze_conversation(messages, {"size": 1, "overlap": 0}, {})
            results.append(json.dumps(result, sort_keys=True))

        # All results should be identical
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i])

    def test_windowing_reproducibility(self):
        """Test that windowing produces reproducible results."""
        messages = [
            {"id": f"m{i}", "ts": f"2025-07-01T09:{i:02d}:00", "speaker": "A", "text": f"Message {i}"}
            for i in range(10)
        ]

        # Test with different window configurations
        result1 = self.engine.analyze_conversation(messages, {"size": 5, "overlap": 0}, {})
        result2 = self.engine.analyze_conversation(messages, {"size": 5, "overlap": 0}, {})

        # Results should be identical
        self.assertEqual(len(result1["hits"]), len(result2["hits"]))

    def test_activation_rules(self):
        """Test various activation rules."""
        # Test ANY rule
        messages = [
            {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker": "A", "text": "Ich bin wütend"},
        ]

        result = self.engine.analyze_conversation(messages, {"size": 1, "overlap": 0}, {})

        # Should contain ATO_ANGER if activated
        anger_hits = [h for h in result["hits"] if h["marker"] == "ATO_ANGER"]
        self.assertGreater(len(anger_hits), 0)

    def test_evidence_tracking(self):
        """Test that evidence is properly tracked."""
        messages = [
            {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker": "A", "text": "Ich bin wütend"},
        ]

        result = self.engine.analyze_conversation(messages, {"size": 1, "overlap": 0}, {})

        # Check that hits have evidence information
        for hit in result["hits"]:
            if "evidence" in hit:
                self.assertIsInstance(hit["evidence"], list)

    def test_marker_validation(self):
        """Test that all referenced markers exist."""
        # Check that all composed_of references are valid
        for marker_id, marker in self.engine.markers.items():
            if "composed_of" in marker:
                for composed_id in marker["composed_of"]:
                    self.assertIn(composed_id, self.engine.markers,
                                f"Marker {marker_id} references non-existent {composed_id}")

if __name__ == '__main__':
    unittest.main()
