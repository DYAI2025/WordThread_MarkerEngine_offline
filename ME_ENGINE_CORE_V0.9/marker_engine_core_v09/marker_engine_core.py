#!/usr/bin/env python3
"""
marker_engine_core.py
─────────────────────────────────────────────────────────────────
Lean-Deep 3.4-konformer Engine-Kern.
Lädt Marker-Definitionen (ATO_/SEM_/CLU_/MEMA_ Präfix), wendet Detektoren aus Registry an,
führt Scoring und Fusion nach Master-Schema durch. Gibt strukturierte Ergebnisse.
"""

from pathlib import Path
import yaml
import json
import importlib
import re
import datetime
import numpy as np
from typing import Dict, List, Any, Optional

if __package__:
    from .numeric_normalizer_plugin import NumericNormalizerPlugin
else:
    from numeric_normalizer_plugin import NumericNormalizerPlugin

# --------------------------------------------------------------
PRFX_LEVELS = ("ATO_", "SEM_", "CLU_", "MEMA_")

class MarkerEngine:
    def __init__(self,
                 marker_root: str = "_Marker_5.0",
                 schema_root: str = "schemata",
                 detect_registry: str = "DETECT_/DETECT_registry.json",
                 plugin_root: str = "plugins"):

        # Resolve paths relative to the module directory to be CWD-agnostic
        self._base_dir = Path(__file__).parent.resolve()

        def _resolve(p: str) -> Path:
            pth = Path(p)
            return (self._base_dir / pth).resolve() if not pth.is_absolute() else pth

        self.marker_path     = _resolve(marker_root)
        self.schema_path     = _resolve(schema_root)
        self.plugin_root     = _resolve(plugin_root)
        self.detect_registry = _resolve(detect_registry)

        # interne Caches
        self.markers : Dict[str, Dict[str, Any]] = {}
        self.schemas : Dict[str, Dict[str, Any]] = {}
        self.active_schemas : List[Dict[str, Any]] = []
        self.schema_priority : Dict[str, float] = {}
        self.fusion_mode : str = "multiply"
        self.detectors: List[Dict[str, Any]]     = []
        self.plugins  : Dict[str, Any]           = {}

        self._load_markers()
        self._load_schemata()
        self._load_detectors()

    # ----------------------------------------------------------
    # Loader
    # ----------------------------------------------------------
    def _load_markers(self):
        """Lädt alle Marker aus dem Marker-Verzeichnis."""
        for file in self.marker_path.glob("*.yaml"):
            try:
                data = yaml.safe_load(file.read_text("utf-8"))
                if data and "id" in data:
                    self.markers[data["id"]] = data
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file {file}: {e}")
                continue

    def _load_schemata(self):
        """Lädt alle Schemata + Master-Schema für Fusion/Prioritäten."""
        if not self.schema_path.exists():
            return
        for file in self.schema_path.glob("SCH_*.json"):
            try:
                data = json.loads(file.read_text("utf-8"))
            except Exception:
                continue
            schema_id = data.get("$id") or data.get("id")
            if schema_id:
                self.schemas[schema_id] = data
        master_path = self.schema_path / "MASTER_SCH_CORE.json"
        if master_path.exists():
            master = json.loads(master_path.read_text("utf-8"))
            self.active_schemas = [self.schemas[sch] for sch in master.get("active_schemata", []) if sch in self.schemas]
            self.schema_priority = master.get("priority", {})
            self.fusion_mode = master.get("fusion", "multiply")

    def _load_detectors(self):
        """Lädt alle Detektoren aus Registry, inkl. optionaler Plugins."""
        if self.detect_registry.exists():
            reg = json.loads(self.detect_registry.read_text("utf-8"))
            # Sort detectors by priority and then by id
            sorted_detectors = sorted(reg.get("detectors", []), key=lambda x: (x.get("priority", 99), x.get("id")))
            for entry in sorted_detectors:
                self.detectors.append(entry)
                if entry.get("module") == "plugin":
                    rel = Path(entry["file_path"])  # may be relative to module dir
                    plugin_path = (self._base_dir / rel).resolve()
                    spec = importlib.util.spec_from_file_location(entry["id"], plugin_path)
                    mod  = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)  # type: ignore
                    self.plugins[entry["id"]] = mod

        # Load custom detectors
        self.detectors.append({"id": "plugin.numeric.normalizer", "module": "custom", "priority": 2})
        self.plugins["plugin.numeric.normalizer"] = NumericNormalizerPlugin()


    # ----------------------------------------------------------
    # Haupt­methode
    # ----------------------------------------------------------
    def analyze(self, text: str, hits: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if hits is None:
            hits = []

        # 1) Detector-Registry anwenden (Präfix-Fire)
        for det in self.detectors:
            if det.get("module") == "regex":
                file_path = Path(det["file_path"])
                if not file_path.is_absolute():
                    file_path = (self._base_dir / file_path).resolve()
                spec = json.loads(file_path.read_text("utf-8"))
                pattern = re.compile(spec["rule"]["pattern"], re.IGNORECASE)
                if pattern.search(text):
                    hits.append({"marker": spec["fires_marker"], "source": det["id"]})

            elif det.get("module") == "plugin":
                plugin = self.plugins[det["id"]]
                result = plugin.run(text)
                hits.extend({"marker": m, "source": det["id"]} for m in result.get("fires", []))
            elif det.get("module") == "custom":
                plugin = self.plugins[det["id"]]
                result = plugin.run(text)
                if isinstance(result, dict) and "fires" in result:
                    hits.extend({"marker": m, "source": det["id"]} for m in result.get("fires", []))
                elif isinstance(result, list):
                    hits.extend(result)
                else:
                    hits.append(result)

        # 2) Pattern-basierte Marker (nur Level 1, atomic)
        for marker_id, marker in self.markers.items():
            if marker_id.startswith("ATO_") and "pattern" in marker:
                pats = marker.get("pattern", [])
                if isinstance(pats, str): pats = [pats]
                for pat in pats:
                    if pat and re.search(pat, text, re.IGNORECASE):
                        hits.append({"marker": marker_id, "source": "pattern"})
                        break

        # 3) Schema-Fusion (Scoring/Priorisierung)
        final_scores: Dict[str, float] = {}
        for hit in hits:
            m = self.markers.get(hit["marker"])
            if not m: continue

            scoring = m.get("scoring", {})
            base = scoring.get("base", 1.0)
            weight = scoring.get("weight", 1.0)
            decay = scoring.get("decay", 0.0)
            formula = scoring.get("formula", "linear")

            if formula == "linear":
                raw = base * weight
            elif formula == "logistic":
                raw = base * (1 / (1 + np.exp(-weight)))
            else:
                raw = base * weight

            for sch in self.active_schemas:
                prio = self.schema_priority.get(Path(sch["id"]).name + ".json", 1.0)
                if self.fusion_mode == "multiply":
                    raw *= prio
                elif self.fusion_mode == "sum":
                    raw += prio

            final_scores[hit["marker"]] = final_scores.get(hit["marker"], 0) + raw

        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "hits": hits,
            "scores": final_scores
        }

    def analyze_conversation(self, messages: List[Dict[str, Any]], window: Dict[str, int], options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes a conversation with a sliding window."""
        all_hits = []
        window_size = window.get("size", 30)
        overlap = window.get("overlap", 0)

        # Create sliding windows
        for i in range(0, len(messages), window_size - overlap):
            chunk = messages[i:i + window_size]
            if len(chunk) < window_size // 2:  # Skip very small chunks
                continue

            text = " ".join([m["text"] for m in chunk])
            result = self.analyze(text)

            # Add message IDs to hits for evidence tracking
            for hit in result["hits"]:
                hit["msg_ids"] = [m["id"] for m in chunk]
                hit["span"] = ""  # Could be enhanced to include actual text spans

            all_hits.extend(result["hits"])

        # Activation Engine with evidence cascade
        activated_markers = []
        for marker_id, marker in self.markers.items():
            activation = marker.get("activation")
            if not activation:
                continue
            rule = activation.get("rule")
            params = activation.get("params", {})
            composed_of = marker.get("composed_of", [])

            if rule == "ANY":
                count = 0
                triggering_hits = []
                for hit in all_hits:
                    if hit["marker"] in composed_of:
                        count += 1
                        triggering_hits.append(hit)
                if count >= params.get("count", 1):
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "ALL":
                present = all(any(hit["marker"] == c for hit in all_hits) for c in composed_of)
                if present:
                    triggering_hits = [hit for hit in all_hits if hit["marker"] in composed_of]
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "AT_LEAST":
                count = 0
                triggering_hits = []
                for hit in all_hits:
                    if hit["marker"] in composed_of:
                        count += 1
                        triggering_hits.append(hit)
                if count >= params.get("count", 1):
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "WEIGHTED_AND":
                # Implement weighted AND logic
                total_weight = 0.0
                triggering_hits = []
                for component in composed_of:
                    component_hits = [hit for hit in all_hits if hit["marker"] == component]
                    if component_hits:
                        # Get weight from combination or default to 1.0
                        weight = 1.0
                        if "combination" in marker and "components" in marker["combination"]:
                            for comp in marker["combination"]["components"]:
                                if isinstance(comp, dict) and comp.get("marker_id") == component:
                                    weight = comp.get("weight", 1.0)
                                    break
                        total_weight += weight
                        triggering_hits.extend(component_hits)

                threshold = params.get("threshold", 0.5)
                if total_weight >= threshold:
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "X_OF_Y":
                # Implement X of Y logic
                x = params.get("x", 1)
                y = params.get("y", len(composed_of))
                present_count = 0
                triggering_hits = []

                for component in composed_of:
                    component_hits = [hit for hit in all_hits if hit["marker"] == component]
                    if component_hits:
                        present_count += 1
                        triggering_hits.extend(component_hits)

                if present_count >= x:
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "SUM_WEIGHT":
                # Implement sum weight logic
                total_weight = 0.0
                triggering_hits = []

                for component in composed_of:
                    component_hits = [hit for hit in all_hits if hit["marker"] == component]
                    if component_hits:
                        # Get weight from combination or default to 1.0
                        weight = 1.0
                        if "combination" in marker and "components" in marker["combination"]:
                            for comp in marker["combination"]["components"]:
                                if isinstance(comp, dict) and comp.get("marker_id") == component:
                                    weight = comp.get("weight", 1.0)
                                    break
                        total_weight += weight * len(component_hits)
                        triggering_hits.extend(component_hits)

                threshold = params.get("threshold", 1.0)
                if total_weight >= threshold:
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "AT_LEAST_DISTINCT":
                # Implement distinct component logic
                distinct_components = set()
                triggering_hits = []

                for hit in all_hits:
                    if hit["marker"] in composed_of:
                        distinct_components.add(hit["marker"])
                        triggering_hits.append(hit)

                if len(distinct_components) >= params.get("count", 1):
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": triggering_hits,
                        "rule": rule,
                        "params": params
                    })
            elif rule == "FREQUENCY":
                # Implement frequency logic
                count = params.get("count", 1)
                window_size = params.get("window", 5)  # Default window of 5 messages

                # Count occurrences in recent messages (simplified)
                recent_hits = [hit for hit in all_hits if hit["marker"] in composed_of]

                if len(recent_hits) >= count:
                    activated_markers.append({
                        "marker_id": marker_id,
                        "source": "activation",
                        "evidence": recent_hits,
                        "rule": rule,
                        "params": params
                    })

        # Add activated markers to hits
        for activated in activated_markers:
            evidence_ids: List[str] = []
            for ev in activated["evidence"]:
                if isinstance(ev, dict) and "msg_ids" in ev:
                    evidence_ids.extend(ev["msg_ids"])
            if not evidence_ids:
                # Fallback: use ids from composed components if available
                for ev in activated["evidence"]:
                    candidate = ev.get("message_id") if isinstance(ev, dict) else None
                    if candidate:
                        evidence_ids.append(candidate)
            all_hits.append({
                "marker": activated["marker_id"],
                "source": activated["source"],
                "evidence": activated["evidence"],
                "rule": activated["rule"],
                "params": activated["params"],
                "msg_ids": list(dict.fromkeys(evidence_ids)) if evidence_ids else []
            })

        # Final Aggregation and Scoring
        aggregates = {}
        total_score = 0
        for hit in all_hits:
            marker_id = hit.get("marker")
            if marker_id:
                aggregates[marker_id] = aggregates.get(marker_id, 0) + 1

        # Simple overall score
        scores = {"overall_intensity": len(all_hits)}

        # Generate Drift Data
        timestamps = sorted([
            (datetime.datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00")).timestamp() if isinstance(m["timestamp"], str) else m["timestamp"])
            for m in messages if "timestamp" in m
        ])
        # Create a simple intensity curve based on hit frequency
        values = np.zeros(len(timestamps))
        if all_hits and timestamps:
            hit_timestamps = []
            for hit in all_hits:
                # Find the timestamp of the first message in the evidence
                if "msg_ids" in hit and hit["msg_ids"]:
                    msg_id = hit["msg_ids"][0]
                    for m in messages:
                        if m["id"] == msg_id:
                            ts = m["timestamp"]
                            if isinstance(ts, str):
                                hit_timestamps.append(datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                            else:
                                hit_timestamps.append(ts)
                            break

            if hit_timestamps:
                # Create a histogram of hits over time
                hist, _ = np.histogram(hit_timestamps, bins=len(timestamps), range=(min(timestamps), max(timestamps)))
                values = np.cumsum(hist) # Cumulative intensity

        drift = {
            "timestamps": list(timestamps),
            "values": values.tolist()
        }

        # Reformat hits to match the final schema
        final_hits = []
        for hit in all_hits:
            if "marker" in hit and "msg_ids" in hit and hit["msg_ids"]:
                final_hit = {
                    "marker": hit["marker"],
                    "marker_id": hit["marker"],
                    "message_id": hit["msg_ids"][0], # Link to the first message in the chunk
                    "score": 1.0, # Placeholder score
                    "source": hit.get("source"),
                    "rule": hit.get("rule"),
                    "params": hit.get("params")
                }
                evidence = hit.get("evidence")
                if isinstance(evidence, list):
                    final_hit["evidence"] = evidence
                final_hits.append(final_hit)

        return {
            "hits": final_hits,
            "aggregates": aggregates,
            "scores": scores,
            "drift": drift
        }

# -----------------------------------------------------------------
if __name__ == "__main__":
    eng = MarkerEngine()
    sample = "Ich weiß normalerweise, was ich will, aber hier bin ich mir nicht sicher. 50k"
    import pprint
    pprint.pprint(eng.analyze(sample))
