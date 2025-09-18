from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import json

class Hit(BaseModel):
    """Schema for individual marker hits"""
    id: str = Field(..., description="Unique hit identifier")
    marker_id: str = Field(..., description="Marker identifier (ATO/SEM/CLU/MEMA)")
    ts: float = Field(..., description="Timestamp")
    conv: Optional[str] = Field(None, description="Conversation identifier")
    payload: Optional[Dict[str, Any]] = Field(None, description="Additional hit data")
    
    class Config:
        extra = "forbid"

class AnalysisBundle(BaseModel):
    """Schema for AnalysisBundle v1.0 validation"""
    bundle: str = Field(..., description="Bundle identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Analysis context")
    input: Optional[Dict[str, Any]] = Field(None, description="Input parameters")
    hits: List[Hit] = Field(..., description="Marker hits")
    aggregates: Optional[Dict[str, Any]] = Field(None, description="Aggregate data")
    scores: Optional[Dict[str, Any]] = Field(None, description="Scoring results")
    drift: Optional[Dict[str, Any]] = Field(None, description="Drift analysis")
    provenance: Optional[Dict[str, Any]] = Field(None, description="Data provenance")
    
    @validator('hits')
    def validate_hits(cls, v):
        """Ensure hits contain required marker structure"""
        if not v:
            raise ValueError("Hits array cannot be empty")
        
        # Check for required marker types
        marker_ids = [hit.marker_id for hit in v]
        if not marker_ids:
            raise ValueError("No marker IDs found in hits")
        
        return v
    
    @validator('bundle')
    def validate_bundle_format(cls, v):
        """Validate bundle identifier format"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Bundle identifier cannot be empty")
        return v.strip()
    
    class Config:
        extra = "forbid"
        schema_extra = {
            "example": {
                "bundle": "analysis_2024_001",
                "context": {"version": "1.0", "source": "marker-engine"},
                "hits": [
                    {
                        "id": "hit_001",
                        "marker_id": "ATO_GREETING",
                        "ts": 1672531200.0,
                        "conv": "conv_001",
                        "payload": {"confidence": 0.95}
                    }
                ],
                "aggregates": {"total_markers": 1},
                "scores": {"overall_confidence": 0.95}
            }
        }

def validate_marker_architecture(hits: List[Hit]) -> Dict[str, Any]:
    """Validate marker architecture compliance (ATO → SEM → CLU → MEMA)"""
    validation_result = {
        "valid": True,
        "warnings": [],
        "architecture_stats": {}
    }
    
    # Categorize markers by type
    marker_types = {
        "ATO": [],
        "SEM": [],
        "CLU": [],
        "MEMA": []
    }
    
    for hit in hits:
        marker_id = hit.marker_id
        if marker_id.startswith("ATO_"):
            marker_types["ATO"].append(marker_id)
        elif marker_id.startswith("SEM_"):
            marker_types["SEM"].append(marker_id)
        elif marker_id.startswith("CLU_"):
            marker_types["CLU"].append(marker_id)
        elif marker_id.startswith("MEMA_"):
            marker_types["MEMA"].append(marker_id)
        else:
            validation_result["warnings"].append(f"Unknown marker type for: {marker_id}")
    
    # Check architecture compliance
    validation_result["architecture_stats"] = {
        level: len(set(markers)) for level, markers in marker_types.items()
    }
    
    # Validate SEM markers have ≥2 distinct ATO references
    # (This would require additional schema information not available in hits alone)
    if len(marker_types["SEM"]) > 0 and len(marker_types["ATO"]) < 2:
        validation_result["warnings"].append("SEM markers present but insufficient ATO markers for composition")
    
    return validation_result
