
class NumericNormalizerPlugin:
    def run(self, text):
        # Mock implementation
        if "50k" in text:
            return {
                "fires": ["ATO_NUMERIC_ESTIMATE"],
                "payload": {
                    "original_text": "50k",
                    "normalized_numeric_value": 50000
                }
            }
        return {"fires": [], "payload": {}}
