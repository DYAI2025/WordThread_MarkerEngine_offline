"""
api_service.py
FastAPI service for the Marker Engine with endpoints for analysis, scoring, and drift.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
from pathlib import Path
import os

from marker_engine_core import MarkerEngine
from scoring_adapter import run_scoring
from drift_axes import DriftAxesManager
from engine_digest import generate_engine_digest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for artifacts (consider using a database in production)
ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Marker Engine API")
    try:
        global engine, drift_manager
        engine = MarkerEngine()
        drift_manager = DriftAxesManager()
        logger.info("Components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Marker Engine API")

app = FastAPI(
    title="Marker Engine API",
    description="API for conversation analysis, scoring, and drift detection",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware with restricted origins
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Data models
class Message(BaseModel):
    id: str
    ts: str
    speaker: str
    text: str

class ConversationRequest(BaseModel):
    messages: List[Message]
    window: Dict[str, int] = {"size": 30, "overlap": 0}
    options: Dict[str, Any] = {"locale": "de-DE", "timezone": "Europe/Berlin"}

    @validator('messages')
    def validate_messages(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one message is required')
        return v

class AnalysisResponse(BaseModel):
    timestamp: str
    summary: str
    hits: List[Dict[str, Any]]
    scores: Dict[str, float]
    drift_values: Dict[str, float]
    drift_events: List[Dict[str, Any]]
    engine_digest: str

# Initialize components
engine = MarkerEngine()
drift_manager = DriftAxesManager()

# Data models
class Message(BaseModel):
    id: str
    ts: str
    speaker: str
    text: str

class ConversationRequest(BaseModel):
    messages: List[Message]
    window: Dict[str, int] = {"size": 30, "overlap": 0}
    options: Dict[str, Any] = {"locale": "de-DE", "timezone": "Europe/Berlin"}

    @validator('messages')
    def validate_messages(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one message is required')
        return v

class AnalysisResponse(BaseModel):
    timestamp: str
    summary: str
    hits: List[Dict[str, Any]]
    scores: Dict[str, float]
    drift_values: Dict[str, float]
    drift_events: List[Dict[str, Any]]
    engine_digest: str

# Global storage for artifacts (in production, use proper database)
artifacts = {}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_conversation(request: ConversationRequest, background_tasks: BackgroundTasks):
    """Analyze a conversation for markers, scores, and drift."""
    try:
        # Convert messages to engine format
        messages = [
            {
                "id": msg.id,
                "ts": msg.ts,
                "speaker": msg.speaker,
                "text": msg.text
            }
            for msg in request.messages
        ]

        # Run analysis
        result = engine.analyze_conversation(messages, request.window, request.options)

        # Run scoring
        scoring_result = run_scoring(messages, result)

        # Calculate drift
        aggregated_scores = {}
        if "aggregated_scores" in scoring_result:
            aggregated_scores = scoring_result["aggregated_scores"]

        drift_values = drift_manager.calculate_drift_values(aggregated_scores)
        drift_events = drift_manager.check_thresholds(drift_values)

        # Generate engine digest
        engine_digest = hashlib.sha256(json.dumps({
            "markers": list(engine.markers.keys()),
            "detectors": [d.get("id") for d in engine.detectors],
            "timestamp": datetime.utcnow().isoformat()
        }).encode()).hexdigest()

        # Prepare response
        response = AnalysisResponse(
            timestamp=datetime.utcnow().isoformat(),
            summary=result["summary"],
            hits=result["hits"],
            scores=result.get("scores", {}),
            drift_values=drift_values,
            drift_events=[
                {
                    "axis_id": event.axis_id,
                    "axis_name": event.axis_name,
                    "value": event.value,
                    "threshold": event.threshold,
                    "direction": event.direction,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.metadata
                }
                for event in drift_events
            ],
            engine_digest=engine_digest
        )

        # Store artifact (write-once)
        input_hash = hashlib.sha256(json.dumps([msg.dict() for msg in request.messages]).encode()).hexdigest()
        artifacts[input_hash] = {
            "input": request.dict(),
            "output": response.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }

        return response

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/scores")
async def get_scores():
    """Get current scoring models and their definitions."""
    return {
        "models": list(engine.models.keys()) if hasattr(engine, 'models') else [],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/drift")
async def get_drift():
    """Get current drift axes and active events."""
    return {
        "axes": drift_manager.axes_definitions,
        "active_events": [
            {
                "axis_id": event.axis_id,
                "axis_name": event.axis_name,
                "value": event.value,
                "threshold": event.threshold,
                "direction": event.direction,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata
            }
            for event in drift_manager.get_active_events()
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/artifacts/{input_hash}")
async def get_artifact(input_hash: str):
    """Retrieve stored analysis artifact by input hash."""
    if input_hash not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifacts[input_hash]

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    logger.info("Starting Marker Engine API...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Marker Engine API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
