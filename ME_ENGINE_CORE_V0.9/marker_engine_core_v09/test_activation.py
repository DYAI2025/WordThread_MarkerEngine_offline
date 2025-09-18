
import unittest
from marker_engine_core import MarkerEngine

class TestActivation(unittest.TestCase):

    def setUp(self):
        self.engine = MarkerEngine()

    def test_any_activation(self):
        messages = [
            {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker":"A", "text":"Ich bin wütend"},
        ]
        result = self.engine.analyze_conversation(messages, {"size": 1, "overlap": 0}, {})
        self.assertIn("ATO_ANGER", [hit["marker"] for hit in result["hits"]])

    def test_all_activation(self):
        # This test will fail because the activation logic for ALL is not fully implemented yet
        messages = [
            {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker":"A", "text":"Ich bin wütend und traurig"},
        ]
        self.engine.markers["CLU_EMOTIONAL_COMPLEXITY"] = {
            "id": "CLU_EMOTIONAL_COMPLEXITY",
            "composed_of": ["ATO_ANGER", "ATO_SADNESS"],
            "activation": {"rule": "ALL"}
        }
        result = self.engine.analyze_conversation(messages, {"size": 1, "overlap": 0}, {})
        self.assertIn("CLU_EMOTIONAL_COMPLEXITY", [hit["marker"] for hit in result["hits"]])

if __name__ == '__main__':
    unittest.main()
