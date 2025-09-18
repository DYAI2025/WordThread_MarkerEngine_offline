import yaml
import json
from pathlib import Path

def resolve_and_validate():
    """
    Loads all markers and the detector registry, then validates all references.
    """
    marker_path = Path("_Marker_5.0")
    detector_registry_path = Path("DETECT_/DETECT_registry.json")

    marker_files = list(marker_path.glob("*.yaml"))
    marker_ids = set()
    markers = {}

    # First pass: get all marker IDs
    for file in marker_files:
        try:
            data = yaml.safe_load(file.read_text("utf-8"))
            if data and "id" in data:
                marker_ids.add(data["id"])
                markers[data["id"]] = data
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file}: {e}")
            continue

    print(f"Loaded {len(marker_ids)} marker IDs.")

    # Validate composed_of references
    missing_composed_of = []
    for marker_id, marker_data in markers.items():
        if "composed_of" in marker_data and marker_data["composed_of"]:
            for composed_of_item in marker_data["composed_of"]:
                composed_of_id = None
                if isinstance(composed_of_item, dict):
                    composed_of_id = composed_of_item.get("id")
                elif isinstance(composed_of_item, str):
                    composed_of_id = composed_of_item

                if composed_of_id and composed_of_id not in marker_ids:
                    missing_composed_of.append({
                        "marker_id": marker_id,
                        "missing_ref": composed_of_id,
                        "file": f"_Marker_5.0/{marker_id}.yaml"
                    })

    if missing_composed_of:
        print("\n--- Missing composed_of references (FATAL) ---")
        for error in missing_composed_of:
            print(f"Marker '{error['marker_id']}' in file '{error['file']}' has a missing composed_of reference: '{error['missing_ref']}'")
        raise SystemExit("Preflight failed: Missing composed_of references. Fix before proceeding.")

    # Validate detector registry
    missing_fires_marker = []
    if detector_registry_path.exists():
        registry = json.loads(detector_registry_path.read_text("utf-8"))
        for detector in registry.get("detectors", []):
            if "fires_marker" in detector and detector["fires_marker"] not in marker_ids:
                missing_fires_marker.append({
                    "detector_id": detector["id"],
                    "missing_ref": detector["fires_marker"]
                })
    else:
        print(f"\n--- Detector registry not found at {detector_registry_path} ---")


    if missing_fires_marker:
        print("\n--- Missing fires_marker references in detector registry (FATAL) ---")
        for error in missing_fires_marker:
            print(f"Detector '{error['detector_id']}' has a missing fires_marker reference: '{error['missing_ref']}'")
        raise SystemExit("Preflight failed: Missing fires_marker references. Fix before proceeding.")
    else:
        print("\n--- fires_marker references in detector registry are all valid. ---")

if __name__ == "__main__":
    resolve_and_validate()