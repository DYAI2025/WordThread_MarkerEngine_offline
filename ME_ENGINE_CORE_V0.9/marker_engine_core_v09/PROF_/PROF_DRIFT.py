"""
PROF_EWMA_DRIFT.py
Live-Tracker, der per Exponentially-Weighted Moving Average (EWMA)
einen Drift-Wert aktualisiert und ab einem Schwellwert Alarm schlägt.
"""

class EWMADrift:
    def __init__(self, alpha=0.3, threshold=0.8):
        self.alpha = alpha
        self.threshold = threshold
        self.mean = None

    def update(self, score: float) -> float:
        """Feed a new score, return updated EWMA."""
        self.mean = score if self.mean is None else (
            self.alpha * score + (1 - self.alpha) * self.mean
        )
        return self.mean

    def drifted(self) -> bool:
        """True ⇢ EWMA >= threshold."""
        return self.mean is not None and self.mean >= self.threshold
