import argparse
import json
from datetime import datetime, timezone
import jsonschema

# Annahme: Die Kern-Engine-Klasse befindet sich hier
from marker_engine_core_v09.marker_engine_core import MarkerEngine

def validate_schema(instance, schema):
    """Generic schema validation function."""
    try:
        jsonschema.validate(instance=instance, schema=schema)
        return True, ""
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message

def main():
    parser = argparse.ArgumentParser(description="Marker Engine Core Processor")
    parser.add_argument("--input", required=True, help="Path to the input PromatraHandshake.json file.")
    parser.add_argument("--output", required=True, help="Path to the output AnalysisBundle.json file.")
    parser.add_argument("--handshake-schema", required=True, help="Path to the PromatraHandshake JSON schema.")
    parser.add_argument("--bundle-schema", required=True, help="Path to the AnalysisBundle JSON schema.")
    args = parser.parse_args()

    # 1. Lade und validiere den Input (PromatraHandshake)
    print(f"Loading handshake file: {args.input}")
    with open(args.input, 'r') as f:
        handshake_data = json.load(f)
    
    with open(args.handshake_schema, 'r') as f:
        handshake_schema_data = json.load(f)

    is_valid, error_msg = validate_schema(handshake_data, handshake_schema_data)
    if not is_valid:
        print(f"Input validation failed: {error_msg}")
        return
    print("Input PromatraHandshake is valid.")

    # 2. Führe die Kern-Analyse aus
    print("Initializing Marker Engine and running analysis...")
    engine = MarkerEngine()
    # Die `analyze_conversation` Methode muss angepasst werden, um die 'messages' zu akzeptieren
    analysis_results = engine.analyze_conversation(
        handshake_data["messages"],
        window={"size": 30, "overlap": 5},  # Default window settings
        options={}  # Default options
    )

    # 3. Baue das AnalysisBundle zusammen
    bundle = {
        "metadata": {
            "source_file": handshake_data["metadata"]["source_file"],
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "analysis_bundle_v1"
        },
        # Die Ergebnisse der Engine müssen den Schlüsseln hier entsprechen
        "hits": analysis_results.get("hits", []),
        "aggregates": analysis_results.get("aggregates", {}),
        "scores": analysis_results.get("scores", {}),
        "drift": analysis_results.get("drift", {})
    }

    # 4. Validiere den Output (AnalysisBundle)
    with open(args.bundle_schema, 'r') as f:
        bundle_schema_data = json.load(f)

    is_valid, error_msg = validate_schema(bundle, bundle_schema_data)
    if not is_valid:
        print(f"Output validation failed: {error_msg}")
        return
    print("Output AnalysisBundle is valid.")

    # 5. Speichere das Ergebnis
    with open(args.output, 'w') as f:
        json.dump(bundle, f, indent=2)
    
    print(f"Successfully created AnalysisBundle at {args.output}")

if __name__ == "__main__":
    main()
