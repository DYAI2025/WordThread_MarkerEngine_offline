# Marker Engine

Deterministic conversation analysis engine with marker detection, scoring, and drift analysis.

## Features

- **Marker Detection**: Pattern-based detection of conversation markers using YAML definitions
- **Activation Rules**: Flexible activation logic (ANY, ALL, AT_LEAST, WEIGHTED_AND, etc.)
- **Scoring Engine**: Multi-dimensional scoring with category weights and severity multipliers
- **Drift Analysis**: Threshold-based monitoring of system changes
- **REST API**: FastAPI-based HTTP service for integration
- **Deterministic Output**: Consistent results across multiple runs

## Architecture

The system follows a modular architecture:

1. **Marker Engine Core**: Loads marker definitions and performs pattern matching
2. **Activation Engine**: Evaluates activation rules for marker composition
3. **Scoring Engine**: Calculates scores based on marker matches
4. **Drift Axes**: Monitors system changes and emits events
5. **API Service**: RESTful interface for external integration

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd marker-engine

# Install dependencies
pip install -r requirements.txt

# Or use modern Python packaging
pip install -e .
```

## Usage

### Basic Analysis

```python
from marker_engine_core import MarkerEngine

engine = MarkerEngine()
messages = [
    {"id": "m1", "ts": "2025-01-01T10:00:00", "speaker": "A", "text": "Hello world"},
    {"id": "m2", "ts": "2025-01-01T10:01:00", "speaker": "B", "text": "How are you?"},
]

result = engine.analyze_conversation(messages, {"size": 2, "overlap": 0}, {})
print(f"Found {len(result['hits'])} marker hits")
```

### Running the API

```bash
# Start the FastAPI server
python -m uvicorn api_service:app --host 0.0.0.0 --port 8000

# Or use the provided script
marker-engine
```

### API Endpoints

- `POST /analyze` - Analyze conversation with complete pipeline
- `POST /scores` - Calculate scores only
- `GET /drift` - Get drift analysis
- `GET /health` - Health check

## Configuration

### Marker Definitions

Markers are defined in YAML files in the `_Marker_5.0/` directory:

```yaml
id: ATO_ANGER_EXPRESSION
version: "3.3"
lang: de
pattern:
  - '(?i)\bwütend\b'
  - '(?i)\bärgerlich\b'
activation:
  rule: ANY
  params:
    count: 1
tags: [emotion, negative]
```

### Scoring Models

Scoring models are defined in `scoring_engine.py` with category weights and thresholds.

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test
python -m pytest test_complete_system.py::TestCompleteSystem::test_end_to_end_analysis
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Linting
flake8 .
```

### Validation

```bash
# Run system validation
python validate_system.py
```

## Project Structure

```
marker-engine/
├── _Marker_5.0/          # Marker definitions
├── DETECT_/              # Detector registry
├── SCH_/                 # Schema definitions
├── api_service.py        # FastAPI service
├── marker_engine_core.py # Core engine
├── scoring_engine.py     # Scoring logic
├── drift_axes.py         # Drift analysis
├── validate_system.py    # System validation
├── test_*.py            # Test files
├── requirements.txt      # Dependencies
├── pyproject.toml       # Modern Python packaging
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Architecture Documentation

See [Zielarchitektur.md](Zielarchitektur.md) for detailed architecture documentation.
