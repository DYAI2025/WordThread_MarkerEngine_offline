#!/usr/bin/env python3
"""
marker_engine_core.py
─────────────────────────────────────────────────────────────────
Lädt Marker-Definitionen, wendet Detektoren an, führt Scoring
und Schema-Fusion durch. Ergebnis ist eine strukturierte Liste
von Marker-Hits inkl. gewichteter Scores.

Ordner-Konvention (siehe README):
• markers/atomic/     A_*.yaml
• markers/semantic/   S_*.yaml
• markers/cluster/    C_*.yaml
• markers/meta/       MM_*.yaml
• schemata/           SCH_*.json  + MASTER_SCH_*.json
• detect/             DETECT_*.json
• grabber_meta/       GR_META_*.json
• plugins/            GR_*.py | .js

Kompatibel mit LeanDeep 3.4
"""

from pathlib import Path
import yaml, json, importlib, re, datetime
from typing import Dict, List, Any

# --------------------------------------------------------------
class MarkerEngine:
    def __init__(self,
                 marker_root: str = "markers",
                 schema_root: str = "schemata",
                 detect_root: str = "detect",
                 grabber_meta_root: str = "grabber_meta",
                 plugin_root: str = "plugins"):

        self.marker_path   = Path(marker_root)
        self.schema_path   = Path(schema_root)
        self.detect_path   = Path(detect_root)
        self.meta_path     = self.marker_path / "meta"          # korrigiert
        self.plugin_root   = Path(plugin_root)
        self.grabber_meta  = Path(grabber_meta_root)

        # interne Caches
        self.markers : Dict[str, Dict[str, Any]] = {}
        self.schemas : Dict[str, Dict[str, Any]] = {}
        self.detectors: List[Dict[str, Any]]     = []
        self.plugins  : Dict[str, Any]           = {}

        self._load_markers()
        self._load_schemata()
        self._load_detectors()

    # ----------------------------------------------------------
    # Loader
    # ----------------------------------------------------------
    def _load_markers(self):
        for level in ["atomic", "semantic", "cluster", "meta"]:
            for file in (self.marker_path / level).glob("*.yaml"):
                data = yaml.safe_load(file.read_text("utf-8"))
                self.markers[data["id"]] = data

    def _load_schemata(self):
        for file in self.schema_path.glob("SCH_*.json"):
            data = json.loads(file.read_text("utf-8"))
            self.schemas[data["id"]] = data

        # aktiver Master-Router
        master = json.loads((self.schema_path / "MASTER_SCH_CORE.json").read_text("utf-8"))
        self.active_schemas = [self.schemas[sch] for sch in master["active_schemata"]]
        self.schema_priority = master["priority"]
        self.fusion_mode = master.get("fusion", "multiply")

    def _load_detectors(self):
        reg = json.loads((self.detect_path / "detector_registry.json").read_text("utf-8"))
        for entry in reg:
            self.detectors.append(entry)
            # optional Plugin laden
            if entry["module"] == "plugin":
                plugin_path = (self.plugin_root / Path(entry["file_path"]).name)
                spec = importlib.util.spec_from_file_location(entry["id"], plugin_path)
                mod  = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                self.plugins[entry["id"]] = mod

    # ----------------------------------------------------------
    # Haupt­methode
    # ----------------------------------------------------------
    def analyze(self, text: str) -> Dict[str, Any]:
        hits: List[Dict[str, Any]] = []

        # 1) Data-Driven Detektoren -----------------------------------------
        for det in self.detectors:
            if det["module"] == "regex":
                spec = json.loads(Path(det["file_path"]).read_text("utf-8"))
                pattern = re.compile(spec["rule"]["pattern"], re.IGNORECASE)
                if pattern.search(text):
                    hits.append({"marker": spec["fire_marker"], "source": det["id"]})

            elif det["module"] == "stddev":
                # Placeholder – echte Implementierung nutzt Feature-Stream
                pass

            elif det["module"] == "plugin":
                plugin = self.plugins[det["id"]]
                result = plugin.run(text)
                hits.extend({"marker": m, "source": det["id"]} for m in result["fire"])

        # 2) Marker-Rules (pattern & activation_logic) ----------------------
        for marker_id, marker in self.markers.items():
            if marker["level"] == 1 and "pattern" in marker:
                for pat in marker["pattern"]:
                    if re.search(pat, text, re.IGNORECASE):
                        hits.append({"marker": marker_id, "source": "pattern"})
                        break  # einmal reicht

        # 3) Schema-Fusion --------------------------------------------------
        final_scores: Dict[str, float] = {}
        for hit in hits:
            m = self.markers[hit["marker"]]
            weight = m.get("scoring", {}).get("weight", 1.0)
            raw = 1.0 * weight

            for sch in self.active_schemas:
                prio = self.schema_priority.get(Path(sch["id"]).name + ".json", 1.0)
                if self.fusion_mode == "multiply":
                    raw *= prio
                elif self.fusion_mode == "sum":
                    raw += prio

            final_scores[hit["marker"]] = final_scores.get(hit["marker"], 0) + raw

        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "hits": hits,
            "scores": final_scores
        }

# -----------------------------------------------------------------
if __name__ == "__main__":
    eng = MarkerEngine()
    sample = "Ich weiß normalerweise, was ich will, aber hier bin ich mir nicht sicher."
    print(json.dumps(eng.analyze(sample), indent=2, ensure_ascii=False))
