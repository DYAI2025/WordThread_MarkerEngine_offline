from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List


def process(input_path: str, models: str, bundle: str, fast: bool = True, timeout_s: int = 10) -> Dict[str, Any]:
    """
    Marker-Engine Core (stabil):
    - Text: .txt/.md direkt lesen, keine STT
    - Audio: STT versuchen (transcribe), bei Fehler weiter ohne transcript/segments
    - Detektoren: Delegation an engine.core.process (Prosodie etc.)
    - Liefert konsistentes Dict mit transcript/segments/events
    """
    inp = Path(input_path)
    transcript: str = ""
    segments: List[Dict[str, Any]] = []

    # 1) TEXT-PFAD (kein STT)
    if inp.suffix.lower() in (".txt", ".md"):
        try:
            transcript = inp.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[ENGINE-CORE] Text read failed: {e}")
            transcript = ""
        # segments bleiben leer

    # 2) AUDIO-PFAD → STT (falls Assets da)
    else:
        try:
            from engine.stt.ct2_runner import transcribe

            stt = transcribe(str(inp), models_path=models)  # kann EngineError(12) werfen, wenn Assets fehlen
            transcript = (stt or {}).get("text") or ""
            segments = (stt or {}).get("segments") or []
        except Exception as e:
            # Kein Abbruch: Prosodie kann trotzdem auf Audio arbeiten; transcript/segments bleiben ggf. leer
            print(f"[ENGINE-CORE] STT failed: {e}")
            transcript = ""
            segments = []

    # 3) DETEKTOR-ORCHESTRATION (Prosodie/Text/SID etc.) via legacy core
    try:
        from engine.core import process as base_process

        res = base_process(input_path=input_path, models=models, bundle=bundle, fast=fast, timeout_s=timeout_s)
    except Exception as e:
        print(f"[ENGINE-CORE] base_process failed: {e}")
        res = {"events": []}

    # 4) ERGEBNIS NORMALISIEREN
    if not isinstance(res, dict):
        res = {"events": []}

    res: Dict[str, Any] = res  # Typ-Hinweis für Type-Checker

    res.setdefault("session", "local")
    res.setdefault("input", inp.name)
    res["transcript"] = transcript
    res["segments"] = segments
    # res["events"] von base_process (Prosodie etc.)
    return res
