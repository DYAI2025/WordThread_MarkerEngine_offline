# =====================================================================
# GR_SEM_EMO_CONTRAST_DRIFT.py   –   Lean-Deep 3.2-Grabber
# =====================================================================
"""
Erkennt Valence-Kontraste in einem Satz
und feuert Marker-ID 'SEM_EMO_CONTRAST_DRIFT'
"""

import re
from typing import List, Dict, Any

id          = "GR_SEM_EMO_CONTRAST_DRIFT"
description = "Detects pivot from certainty/positive to uncertainty/negative"

# ---------------- Regex-Bausteine -----------------------------------
certainty   = r"(ich weiß|i know|ich bin (mir )?sicher|i am sure|normalerweise|usually)"
uncertainty = r"(weiß (ich )?nicht|i don't know|unsicher|not sure|keine ahnung)"
contrast    = r"\b(aber|jedoch|but|however)\b"
pattern_full = re.compile(f"{certainty}.*{contrast}.*{uncertainty}", re.I)

pos_adj = r"\b(stark|glücklich|gut|strong|happy|good)\b"
neg_adj = r"\b(schwach|verletzt|klein|weak|hurt|small)\b"
pattern_adj  = re.compile(f"{pos_adj}.*{contrast}.*{neg_adj}", re.I)
# --------------------------------------------------------------------

def run(text: str,
        utils: Any = None,
        meta : Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Grabber-Hook – gibt {fire:[id], score:n, details:[]} zurück
    """
    matches: List[Dict[str, str]] = []

    if (m := pattern_full.search(text)):
        matches.append({"rule":"certainty_pivot","snippet":m.group(0)})

    if (m := pattern_adj.search(text)):
        matches.append({"rule":"adj_contrast", "snippet":m.group(0)})

    return {
        "fire":  ["SEM_EMO_CONTRAST_DRIFT"] if matches else [],
        "score": len(matches),
        "details": matches
    }
