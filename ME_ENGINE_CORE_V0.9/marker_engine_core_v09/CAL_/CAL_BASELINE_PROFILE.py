# =====================================================================
# CAL_BASELINE_PROFILE.py   –   Lean-Deep 3.2  (Baseline-Generator)
# =====================================================================
"""
Erzeugt Benutzer-Baseline (Normalverhalten) aus Chat-JSON.

Neue Features (3.2):
•  schema_version 3.2   •  Präfixfreie, reine Statistik
#  emoji-Regex nutzt emoji-package fallback (wenn `regex` keine \\p{Emoji} kennt)
"""

import argparse, json, statistics, datetime, re
from pathlib import Path

try:
    import emoji
    EMOJI_RE = re.compile("|".join(emoji.EMOJI_DATA.keys()))
except ImportError:
    EMOJI_RE = re.compile(r":\w+:")  # Fallback – geringe Genauigkeit

SCHEMA_VERSION = "3.2"

def analyse(messages):
    vals, token_lengths, emoji_total = [], [], 0
    for msg in messages:
        txt = msg.get("text", "")
        # Speaker-Valence sammeln
        if (val := msg.get("speaker_valence")) is not None:
            vals.append(val)
        token_lengths.append(len(txt.split()))
        emoji_total += len(EMOJI_RE.findall(txt))

    return {
        "schema_version": SCHEMA_VERSION,
        "speaker_valence": {
            "mean": statistics.mean(vals) if vals else 0,
            "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0
        },
        "avg_tokens": statistics.mean(token_lengths) if token_lengths else 0,
        "emoji_rate": emoji_total / max(len(messages), 1),
        "generated_at": datetime.datetime.utcnow().isoformat()
    }

def main():
    ap = argparse.ArgumentParser(
        description="Generate Lean-Deep 3.2 baseline profile from chat.json")
    ap.add_argument("--chat", required=True)
    ap.add_argument("--out",  required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.chat).read_text(encoding="utf-8"))
    baseline = analyse(data["messages"])
    Path(args.out).write_text(json.dumps(baseline, indent=2))
    print("✅ Baseline saved to", args.out)

if __name__ == "__main__":
    main()                                                 # 
