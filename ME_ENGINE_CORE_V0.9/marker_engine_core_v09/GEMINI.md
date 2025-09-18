## Project Overview

This project appears to be a Python-based text analysis engine. It is designed to identify and score "markers" within a given text. These markers are defined in YAML files and seem to represent various linguistic and emotional cues, such as anger, blame-shifting, and fear.

The engine is composed of two main components:

*   **`marker_engine_core.py`**: This module is responsible for loading the marker definitions from the YAML files and using regular expressions and other detection methods to find occurrences of these markers in a text.
*   **`scoring_engine.py`**: This module takes the detected markers and calculates various scores, such as a "manipulation index" or "relationship health" score.

The project also appears to support a plugin architecture for extending its detection capabilities.

## Building and Running

**TODO:** The exact commands for building and running the project are not immediately clear from the available files.

However, the `marker_engine_core.py` file can be run as a standalone script, likely for testing purposes:

```bash
python marker_engine_core.py
```

## Development Conventions

*   **Markers**: Markers are defined in YAML files located in the `_Marker_5.0` directory. Each marker has a unique ID, a set of patterns to match, and other metadata.
*   **Scoring**: The scoring logic is implemented in `scoring_engine.py`. It uses a set of predefined models to calculate scores based on the detected markers.
*   **Plugins**: The engine can be extended with plugins. The `DETECT_registry.json` file seems to be used to register these plugins.
