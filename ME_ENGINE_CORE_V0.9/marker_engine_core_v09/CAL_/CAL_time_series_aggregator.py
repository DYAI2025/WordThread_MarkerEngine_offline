class TimeSeriesAggregator:
    """Aggregates scores and marker matches using pluggable calculators."""

    def __init__(
        self,
        config: Optional[AggregationConfig] = None,
        score_calculator: Optional[Any] = None,  # Pluggable calculator
        marker_detector: Optional[Any] = None    # Pluggable detector
    ):
        self.config = config or AggregationConfig()
        self.score_calculator = score_calculator
        self.marker_detector = marker_detector

    def _create_score_point(
        self, scores: List[ChunkScore],
        start: datetime, end: datetime,
        score_type: str
    ) -> TimeSeriesPoint:
        pt = TimeSeriesPoint(
            timestamp=start, period_start=start, period_end=end
        )
        if self.score_calculator:
            pt.values, pt.counts = self.score_calculator(scores)
        else:
            # Default logic (as before)
            if scores:
                vals = [s.normalized_score for s in scores]
                mean = float(np.mean(vals))
                risk = 5 / (1 + np.exp(-0.8*(mean-1)))
                pt.values = {
                    "mean": mean, "min": float(min(vals)), "max": float(max(vals)),
                    "std": float(np.std(vals) if len(vals) > 1 else 0),
                    "median": float(np.median(vals)), "risk_logistic": risk
                }
                pt.counts = {"chunk_count": len(scores)}
            else:
                pt.values = {"mean":0,"min":0,"max":0,
                             "std":0,"median":0,"risk_logistic":0}
                pt.counts = {"chunk_count":0}
        return pt

    # Other methods remain unchanged, but can use self.marker_detector if needed
