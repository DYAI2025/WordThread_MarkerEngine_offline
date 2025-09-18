class EngagementPromptPriority:
    def __init__(self):
        pass

    def get_priority(self, ato_first_person_pronoun_score: float, clu_business_readiness_score: float) -> str:
        if clu_business_readiness_score > 2.0 and ato_first_person_pronoun_score > 0.5:
            return "High: Deep dive into KPIs and execution details."
        elif clu_business_readiness_score > 1.0:
            return "Medium: Focus on business model clarity and financial metrics."
        else:
            return "Low: Explore vision and general understanding."
