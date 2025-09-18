
from numeric_normalizer_plugin import NumericNormalizerPlugin

class NumericDetector:
    id = "plugin.numeric.normalizer"
    fires = ["ATO_NUMERIC_ESTIMATE"]

    def __init__(self):
        self.plugin = NumericNormalizerPlugin()

    def run(self, text):
        out = self.plugin.run(text)
        hits = []
        for m in out.get("fires", []):
            hits.append({
                "marker": m,
                "source": self.id,
                "payload": out.get("payload", {}),
                "evidence": {"span": out["payload"].get("original_text")}
            })
        return hits
