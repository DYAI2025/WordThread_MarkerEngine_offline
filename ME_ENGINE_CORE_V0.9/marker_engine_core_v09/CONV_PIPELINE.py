from datetime import datetime
from marker_engine_core import MarkerEngine
from scoring_adapter import run_scoring

CHAT = [
    {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker":"A", "text":"Du bist süß ;)"},
    {"id": "m2", "ts": "2025-07-01T09:01:00", "speaker":"B", "text":"Nicht verraten!"},
    # ...
]

engine = MarkerEngine() 
engine_output = engine.analyze_conversation(
    messages=CHAT,
    window={"size": 30, "overlap": 0},
    options={"locale":"de-DE","timezone":"Europe/Berlin"}
)

scoring_result = run_scoring(CHAT, engine_output)

import pprint
pprint.pprint(scoring_result)