import yaml
import json
from pathlib import Path

def resolve_and_create_placeholders():
    """
    Loads all markers and the detector registry, validates all references,
    and creates placeholder files for missing markers.
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

    # Find all referenced markers
    referenced_ids = set()
    for marker_id, marker_data in markers.items():
        if "composed_of" in marker_data and marker_data["composed_of"]:
            for composed_of_item in marker_data["composed_of"]:
                composed_of_id = None
                if isinstance(composed_of_item, dict):
                    composed_of_id = composed_of_item.get("id")
                elif isinstance(composed_of_item, str):
                    composed_of_id = composed_of_item
                if composed_of_id:
                    referenced_ids.add(composed_of_id)

    if detector_registry_path.exists():
        registry = json.loads(detector_registry_path.read_text("utf-8"))
        for detector in registry.get("detectors", []):
            if "fires_marker" in detector:
                referenced_ids.add(detector["fires_marker"])

    # Find missing markers
    missing_markers = referenced_ids - marker_ids

    if missing_markers:
        print("\n--- Creating placeholder files for missing markers ---")
        for missing_marker_id in missing_markers:
            if missing_marker_id == "ATO_PLACEHOLDER":
                continue
            placeholder_content = {
                "id": missing_marker_id,
                "description": "This is a placeholder for a missing marker.",
                "tags": ["placeholder"]
            }
            placeholder_file = marker_path / f"{missing_marker_id}.yaml"
            with open(placeholder_file, "w") as f:
                yaml.dump(placeholder_content, f)
            print(f"Created placeholder file: {placeholder_file}")
    else:
        print("\n--- No missing markers found. ---")

if __name__ == "__main__":
    resolve_and_create_placeholders()
