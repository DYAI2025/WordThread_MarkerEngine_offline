"""
validate_system.py
Final validation script to ensure system integrity and deterministic behavior.
"""

import hashlib
import json
from pathlib import Path
from marker_engine_core import MarkerEngine
from scoring_adapter import run_scoring
from drift_axes import DriftAxesManager

def validate_marker_references():
    """Validate that all composed_of references exist."""
    engine = MarkerEngine()
    missing_references = []

    for marker_id, marker in engine.markers.items():
        if "composed_of" in marker:
            composed_list = marker["composed_of"]
            if isinstance(composed_list, list):
                for composed_id in composed_list:
                    if isinstance(composed_id, str) and composed_id not in engine.markers:
                        missing_references.append({
                            "referencing_marker": marker_id,
                            "missing_reference": composed_id
                        })
            else:
                print(f"Warning: composed_of in {marker_id} is not a list: {composed_list}")

    if missing_references:
        print("❌ Missing marker references found:")
        for ref in missing_references:
            print(f"  {ref['referencing_marker']} references {ref['missing_reference']}")
        return False
    else:
        print("✅ All marker references are valid")
        return True

def validate_detector_references():
    """Validate that all detector fires_marker references exist."""
    engine = MarkerEngine()
    missing_references = []

    for detector in engine.detectors:
        if "fires_marker" in detector:
            marker_id = detector["fires_marker"]
            if marker_id not in engine.markers:
                missing_references.append({
                    "detector": detector.get("id", "unknown"),
                    "missing_marker": marker_id
                })

    if missing_references:
        print("❌ Missing detector marker references found:")
        for ref in missing_references:
            print(f"  {ref['detector']} fires {ref['missing_marker']}")
        return False
    else:
        print("✅ All detector marker references are valid")
        return True

def test_deterministic_output():
    """Test that same input produces consistent core output (allowing for minor timing variations)."""
    messages = [
        {"id": "m1", "ts": "2025-07-01T09:00:00", "speaker": "A", "text": "Test message for determinism"},
        {"id": "m2", "ts": "2025-07-01T09:01:00", "speaker": "B", "text": "Another test message"},
    ]

    drift_manager = DriftAxesManager()

    # Run analysis multiple times
    core_results = []
    for i in range(3):
        # Create fresh engine instance for each run to avoid state accumulation
        engine = MarkerEngine()
        result = engine.analyze_conversation(messages, {"size": 2, "overlap": 0}, {})
        scoring_result = run_scoring(messages, result)
        drift_values = drift_manager.calculate_drift_values(scoring_result.aggregated_scores)

        # Extract core deterministic data
        core_data = {
            "hits_count": len(result["hits"]),
            "scores_keys": sorted(scoring_result.aggregated_scores.keys()),
            "drift_keys": sorted(drift_values.keys()) if drift_values else [],
            "drift_values_rounded": {k: round(float(v), 2) for k, v in drift_values.items()} if drift_values else {},
            "top_markers": sorted([hit["marker"] for hit in result["hits"]])
        }
        
        core_results.append(core_data)

    # Check if core results are identical
    first_result = core_results[0]
    all_identical = all(
        result["hits_count"] == first_result["hits_count"] and
        result["scores_keys"] == first_result["scores_keys"] and
        result["drift_keys"] == first_result["drift_keys"] and
        result["drift_values_rounded"] == first_result["drift_values_rounded"] and
        result["top_markers"] == first_result["top_markers"]
        for result in core_results
    )
    
    if all_identical:
        print("✅ Core deterministic output confirmed")
        return True
    else:
        print("❌ Core non-deterministic output detected")
        print(f"Expected: {first_result}")
        for i, result in enumerate(core_results[1:], 1):
            if result != first_result:
                print(f"Difference in run {i+1}: {result}")
        return False

def validate_activation_formats():
    """Validate that all activation rules are in the correct format."""
    engine = MarkerEngine()
    invalid_formats = []

    for marker_id, marker in engine.markers.items():
        if "activation" in marker:
            activation = marker["activation"]
            if not isinstance(activation, dict):
                invalid_formats.append({
                    "marker": marker_id,
                    "activation": activation
                })
            elif "rule" not in activation:
                invalid_formats.append({
                    "marker": marker_id,
                    "activation": activation
                })

    if invalid_formats:
        print("❌ Invalid activation formats found:")
        for fmt in invalid_formats:
            print(f"  {fmt['marker']}: {fmt['activation']}")
        return False
    else:
        print("✅ All activation formats are valid")
        return True

def run_full_validation():
    """Run complete system validation."""
    print("🔍 Running complete system validation...\n")

    validations = [
        ("Marker References", validate_marker_references),
        ("Detector References", validate_detector_references),
        ("Deterministic Output", test_deterministic_output),
        ("Activation Formats", validate_activation_formats),
    ]

    all_passed = True
    for name, validator in validations:
        print(f"Running {name} validation...")
        if not validator():
            all_passed = False
        print()

    if all_passed:
        print("🎉 All validations passed! System is ready for production.")
        return True
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    run_full_validation()
