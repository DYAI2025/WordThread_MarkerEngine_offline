import hashlib
import json
from pathlib import Path

def generate_engine_digest():
    """
    Generates a digest of the engine's configuration.
    """
    marker_path = Path("_Marker_5.0")
    detector_registry_path = Path("DETECT_/DETECT_registry.json")

    marker_files = sorted(list(marker_path.glob("*.yaml")))

    digest_content = ""

    for file in marker_files:
        digest_content += file.read_text("utf-8")

    if detector_registry_path.exists():
        digest_content += detector_registry_path.read_text("utf-8")

    # Include Python source files for reproducibility
    python_files = sorted(list(Path(".").glob("**/*.py")))
    for file in python_files:
        if file.is_file():
            digest_content += file.read_text("utf-8")

    # Include requirements for dependency reproducibility
    req_path = Path("requirements.txt")
    if req_path.exists():
        digest_content += req_path.read_text("utf-8")

    req_lock_path = Path("requirements.lock")
    if req_lock_path.exists():
        digest_content += req_lock_path.read_text("utf-8")

    digest = hashlib.sha256(digest_content.encode("utf-8")).hexdigest()
    print(f"Engine Digest: {digest}")

if __name__ == "__main__":
    generate_engine_digest()
