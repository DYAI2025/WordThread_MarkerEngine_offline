# app/routes/telemetry.py
"""
Intuition Package v3.3 Telemetry Endpoint
Provides real-time metrics for intuition marker performance
"""
from flask import Blueprint, jsonify

bp = Blueprint("telemetry", __name__)

# Replace get() with your actual telemetry store accessor
def get(k, d=0):
    """Get telemetry value - replace with your implementation"""
    # return current_app.telemetry.get(k, d)
    pass

@bp.get("/telemetry/intuition")
def telemetry_intuition():
    """
    Returns intuition marker performance metrics
    UI logic: EWMA ≥ 0.70 → green (loosen); 0.50–0.69 → amber (hold); < 0.50 → red (tighten)
    """
    fams = [
        ("grief",   "INT_GRIEF"),
        ("conflict","INT_CONFLICT"),
        ("support", "INT_SUPPORT"),
        ("commit",  "INT_COMMIT"),
        ("uncert",  "INT_UNCERT"),
    ]
    
    rows = []
    for name, key in fams:
        c = get(f"{key}.confirmed", 0)
        r = get(f"{key}.retracted", 0)
        ew = get(f"{key}.ewma_precision", 0.5)
        rows.append({
            "family": name, 
            "confirmed": c, 
            "retracted": r, 
            "ewma": ew,
            "precision": c / max(1, c+r),
            "status": "green" if ew >= 0.70 else "amber" if ew >= 0.50 else "red"
        })
    
    return jsonify(rows)

@bp.get("/telemetry/intuition/<family>")
def telemetry_intuition_family(family):
    """Get detailed metrics for specific intuition family"""
    family_map = {
        "grief": "INT_GRIEF",
        "conflict": "INT_CONFLICT", 
        "support": "INT_SUPPORT",
        "commit": "INT_COMMIT",
        "uncert": "INT_UNCERT"
    }
    
    if family not in family_map:
        return jsonify({"error": "Unknown family"}), 404
        
    key = family_map[family]
    c = get(f"{key}.confirmed", 0)
    r = get(f"{key}.retracted", 0)
    ew = get(f"{key}.ewma_precision", 0.5)
    
    return jsonify({
        "family": family,
        "confirmed": c,
        "retracted": r, 
        "ewma": ew,
        "precision": c / max(1, c+r),
        "total_triggers": c + r,
        "confidence_level": "high" if ew >= 0.70 else "medium" if ew >= 0.50 else "low"
    })

@bp.get("/telemetry/intuition/dashboard")
def telemetry_dashboard_data():
    """
    Returns formatted dashboard data for UI consumption
    Example panel payload (flat JSON for simple UI)
    """
    return jsonify([
        {"family":"grief","confirmed":12,"retracted":4,"ewma":0.73,"status":"green"},
        {"family":"conflict","confirmed":9,"retracted":11,"ewma":0.45,"status":"red"},
        {"family":"support","confirmed":21,"retracted":3,"ewma":0.82,"status":"green"},
        {"family":"commit","confirmed":7,"retracted":5,"ewma":0.58,"status":"amber"},
        {"family":"uncert","confirmed":14,"retracted":6,"ewma":0.70,"status":"green"}
    ])
