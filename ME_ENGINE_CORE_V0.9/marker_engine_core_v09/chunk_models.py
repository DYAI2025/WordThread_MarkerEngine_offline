
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TextChunk:
    id: str
    text: str
    timestamp: datetime
    speaker: type("Speaker", (), {"name": str})  # quick shim
    word_count: int
