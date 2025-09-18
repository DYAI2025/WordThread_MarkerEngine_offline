import unittest
from marker_engine_core import MarkerEngine
import numpy as np

class TestScoring(unittest.TestCase):

    def setUp(self):
        self.engine = MarkerEngine()

    def test_linear_scoring(self):
        self.engine.markers["TEST_MARKER"] = {
            "id": "TEST_MARKER",
            "scoring": {
                "base": 2.0,
                "weight": 3.0,
                "formula": "linear"
            }
        }
        hits = [{"marker": "TEST_MARKER"}]
        scores = self.engine.analyze("", hits=hits)["scores"]
        self.assertEqual(scores["TEST_MARKER"], 6.0)

    def test_logistic_scoring(self):
        self.engine.markers["TEST_MARKER"] = {
            "id": "TEST_MARKER",
            "scoring": {
                "base": 2.0,
                "weight": 1.0,
                "formula": "logistic"
            }
        }
        hits = [{"marker": "TEST_MARKER"}]
        scores = self.engine.analyze("", hits=hits)["scores"]
        self.assertAlmostEqual(scores["TEST_MARKER"], 2.0 * (1 / (1 + np.exp(-1.0))))

if __name__ == '__main__':
    unittest.main()