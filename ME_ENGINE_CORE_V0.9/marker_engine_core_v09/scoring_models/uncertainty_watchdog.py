class UncertaintyWatchdog:
    def __init__(self):
        self.uncertainty_threshold = 1.0 # Example threshold

    def get_recommendation(self, clu_intuition_uncertainty_score: float, is_confirmed: bool) -> str:
        if is_confirmed and clu_intuition_uncertainty_score > self.uncertainty_threshold:
            return "Reduce aggressive recommendations; enforce 'ask for evidence' followup."
        elif clu_intuition_uncertainty_score > self.uncertainty_threshold:
            return "Consider cautious recommendations; monitor for further uncertainty."
        else:
            return "No specific uncertainty-related recommendations."
