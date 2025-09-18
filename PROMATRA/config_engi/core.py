import json
import os
from pathlib import Path
from typing import Any, Dict, List

from tools.engine_adapter import EngineError


def _load_json(path: Path, default: Any = None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_registry(root: Path) -> List[Dict[str, Any]]:
    cand = [root / "DETECT_registry.json", root / "detectors" / "DETECT_registry.json"]
    for p in cand:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception:
                continue
    # Minimal Default: text + poseid
    return [
        {
            "id": "DET_TEXT_GENERIC",
            "module": "engine.detectors.text.generic",
            "file_path": "engine/detectors/text/generic.py",
            "fires_marker": ["*"],
            "schema_version": "3.4",
        },
        {
            "id": "DET_SID",
            "module": "engine.detectors.audio.sid",
            "file_path": "engine/detectors/audio/sid.py",
            "fires_marker": ["M_SID_SPEAKER_MATCH"],
            "schema_version": "3.4",
        },
    ]


def _load_scoring(root: Path) -> Dict[str, Any]:
    p = root / "scoring" / "SCR_GLOBAL.json"
    return _load_json(p, {
        "schema_version": "3.4",
        "weights": {"negation": 1.0, "intent": 0.9, "risk": 1.2, "action": 0.8, "poseid": 1.5},
        "fusion": {"method": "weighted_sum", "normalize": True, "cap": 1.0},
        "thresholds": {"emit_event": 0.55},
    })


def process(input_path: str, models: str, bundle: str, fast: bool = True, timeout_s: int = 8) -> Dict[str, Any]:
    print("--- in core.process ---")
    root = Path(".")
    inp = Path(input_path)

    registry = _load_registry(root)
    scoring = _load_scoring(root)

    all_events: List[Dict[str, Any]] = []
    for det in registry:
        mod_name = det.get("module")
        if not mod_name:
            continue
        try:
            mod = __import__(mod_name, fromlist=["run"])  # dynamic import
        except Exception:
            # Detector optional; skip silently to keep engine resilient
            continue
        if not hasattr(mod, "run"):
            continue
        try:
            events = mod.run(inp, scoring=scoring)
            if isinstance(events, list):
                all_events.extend(events)
        except EngineError:
            # Detector declared itself unavailable or missing assets; skip
            continue
        except Exception:
            # Detector failure must not crash whole engine; continue.
            continue

    return {"events": all_events}
