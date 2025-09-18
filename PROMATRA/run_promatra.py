import argparse
import json
import uuid
from datetime import datetime
import os
import jsonschema
from promatra_core import process_audio_file # Import from the new core file

def process_text_file(file_path):
    """
    Processes a text file by chunking it into messages.
    """
    print(f"Processing text file: {file_path}")
    messages = []
    with open(file_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            messages.append({
                "id": str(uuid.uuid4()),
                "timestamp": 0.0,
                "text": line.strip(),
                "prosody": None,
                "voice_markers": []
            })
    return messages

def validate_handshake(handshake_data, schema):
    """Validates the generated handshake against the JSON schema."""
    try:
        jsonschema.validate(instance=handshake_data, schema=schema)
        print("Validation successful: PromatraHandshake conforms to the schema.")
        return True
    except jsonschema.exceptions.ValidationError as err:
        print(f"Validation failed: {err.message}")
        return False

def main():
    parser = argparse.ArgumentParser(description="PROMATRA Input Processor")
    parser.add_argument("--input", required=True, help="Path to the input audio or text file.")
    parser.add_argument("--output", required=True, help="Path to the output PromatraHandshake.json file.")
    parser.add_argument("--schema", required=True, help="Path to the PromatraHandshake JSON schema.")
    args = parser.parse_args()

    file_ext = os.path.splitext(args.input)[1].lower()
    
    if file_ext in ['.wav', '.mp3', '.flac', '.m4a']:
        messages = process_audio_file(args.input)
    elif file_ext == '.txt':
        messages = process_text_file(args.input)
    else:
        print(f"Error: Unsupported file type '{file_ext}'.")
        return

    handshake = {
        "metadata": {
            "source_file": os.path.basename(args.input),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "schema_version": "promatra_handshake_v1"
        },
        "messages": messages
    }

    with open(args.schema, 'r') as f:
        schema_data = json.load(f)
    
    if not validate_handshake(handshake, schema_data):
        print("Aborting due to validation failure.")
        return

    with open(args.output, 'w') as f:
        json.dump(handshake, f, indent=2)
    
    print(f"Successfully created PromatraHandshake at {args.output}")

if __name__ == "__main__":
    main()
