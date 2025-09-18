"""
cost_vector_math.py
Grundlegende Vektor-Hilfsfunktionen (Cosinus, Euklid, Normalisierung)
"""

import math
from typing import List

Vector = List[float]

def dot(a: Vector, b: Vector) -> float:
    return sum(x*y for x, y in zip(a, b))

def l2(a: Vector) -> float:
    return math.sqrt(sum(x*x for x in a))

def cosine(a: Vector, b: Vector) -> float:
    denom = l2(a) * l2(b)
    return dot(a, b) / denom if denom else 0.0

def normalize(a: Vector) -> Vector:
    length = l2(a)
    return [x/length for x in a] if length else a
