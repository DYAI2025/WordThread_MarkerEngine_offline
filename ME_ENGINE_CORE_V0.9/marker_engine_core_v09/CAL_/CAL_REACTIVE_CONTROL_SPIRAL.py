# =====================================================================
# CAL_REACTIVE_CONTROL_SPIRAL.py  –  Lean-Deep 3.2  (Detection Helper)
# =====================================================================
"""
Erkennt eskalierende Reaktiv-Kontroll-Spiralen in einer Textsequenz.

• Gibt bool zurück; Matcher kann darauf MEMA/CLU-Marker feuern
• Regex-Listen jetzt UTF-8-safe (raw-Strings, IGNORECASE + DOTALL)
• Keine Abhängigkeit von Präfix-Schema – pure Heuristik
"""

import re
from typing import List

REACTIVE_CONTROL_SPIRAL_PATTERNS: List[str] = [
    r"(du hast angefangen|nein, du hast angefangen|du willst stur sein|"
    r"ich kann sturer sein|jedes mal, wenn ich|toll, weil du eingeschnappt"
    r" bist, bin ich jetzt auch eingeschnappt|ich gehe erst einen schritt, "
    r"wenn du einen gehst|ich senke meinen ton erst, wenn du deinen senkst|"
    r"ich schreie durch die tür|du manipulierst|nein, du zwingst mich dazu|"
    r"wenn du provozierst, kann ich für nichts garantieren|du willst es auf "
    r"die harte tour|solange du dich nicht entschuldigst, entschuldige "
    r"ich mich auch nicht|kontrolle behalten|es endet erst, wenn einer aufgibt)",

    r"(du willst ehrlich sein, okay, hier ist die ehrliche meinung|"
    r"du bist das problem|du willst immer das letzte wort|"
    r"ich hab dir zehnmal geschrieben|ich ignoriere jetzt mal deine anrufe|"
    r"jeder deiner vorwürfe gibt mir nur mehr munition)"
]

PATTERNS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in REACTIVE_CONTROL_SPIRAL_PATTERNS]

def detect_reactive_control_spiral(text: str) -> bool:                   # 
    """True → Muster erkannt"""
    text = text or ""
    return any(p.search(text) for p in PATTERNS)
