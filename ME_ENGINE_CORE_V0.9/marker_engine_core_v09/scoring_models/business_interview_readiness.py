class BusinessInterviewReadinessScoringModel:
    def __init__(self):
        self.weights = {
            "SEM_FINANCIAL_METRICS": 3.0,
            "SEM_BUSINESS_FOCUS": 2.5,
            "SEM_TENTATIVE_INFERENCE": -1.0
        }
        self.thresholds = {
            "warning": 5.0,
            "critical": 2.0
        }

    def calculate_score(self, sem_scores: dict) -> float:
        score = 0.0
        for sem_id, weight in self.weights.items():
            score += sem_scores.get(sem_id, 0.0) * weight
        return score

    def get_followup_priority(self, score: float) -> str:
        if score < self.thresholds["critical"]:
            return "critical: ask for more data, deeper dive into unit economics"
        elif score < self.thresholds["warning"]:
            return "warning: consider asking for more data"
        else:
            return "low: proceed with general questions"
