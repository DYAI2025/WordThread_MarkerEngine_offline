from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import base64
import hashlib

class EvidenceType(str, Enum):
    """Evidence types for PromatraHandshake v0.2"""
    MARKER_WEIGHT = "marker_weight"
    SCORING_WINDOW = "scoring_window"
    SCHEMA_CONFIG = "schema_config"
    TELEMETRY_DATA = "telemetry_data"
    INTUITION_STATE = "intuition_state"
    MULTIPLIER_DATA = "multiplier_data"
    ATTACHMENT_REFERENCE = "attachment_reference"
    BINARY_DATA = "binary_data"

class AttachmentInfo(BaseModel):
    """Information about file attachments"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME content type")
    size_bytes: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 checksum of file")
    encoding: str = Field("base64", description="Content encoding method")
    
    class Config:
        extra = "forbid"

class Evidence(BaseModel):
    """Schema for evidence attachments with enhanced v0.2 features"""
    id: str = Field(..., description="Evidence identifier")
    type: EvidenceType = Field(..., description="Evidence type")
    source: str = Field(..., description="Evidence source")
    data: Dict[str, Any] = Field(..., description="Evidence data")
    attachment_info: Optional[AttachmentInfo] = Field(None, description="Attachment metadata")
    content: Optional[str] = Field(None, description="Base64 encoded content for binary evidence")
    timestamp: Optional[float] = Field(None, description="Evidence creation timestamp")
    
    @validator('content')
    def validate_content_encoding(cls, v, values):
        """Validate base64 encoded content"""
        if v is not None:
            try:
                base64.b64decode(v, validate=True)
            except Exception as e:
                raise ValueError(f"Invalid base64 content encoding: {str(e)}")
        return v
    
    @validator('attachment_info')
    def validate_attachment_checksum(cls, v, values):
        """Validate attachment checksum if content is provided"""
        if v is not None and 'content' in values and values['content'] is not None:
            try:
                decoded_content = base64.b64decode(values['content'])
                calculated_checksum = hashlib.sha256(decoded_content).hexdigest()
                if v.checksum != calculated_checksum:
                    raise ValueError("Attachment checksum mismatch")
            except Exception as e:
                raise ValueError(f"Checksum validation failed: {str(e)}")
        return v
    
    class Config:
        extra = "forbid"

class PromatraHandshake(BaseModel):
    """Schema for PromatraHandshake v0.2 validation with enhanced attachment handling"""
    version: str = Field("0.2", description="Handshake version")
    handshake_id: str = Field(..., description="Unique handshake identifier")
    timestamp: float = Field(..., description="Handshake timestamp")
    attachments: Optional[List[str]] = Field(None, description="Attachment references")
    evidence: Optional[List[Evidence]] = Field(None, description="Evidence objects")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    processing_context: Optional[Dict[str, Any]] = Field(None, description="Processing context information")
    signature: Optional[str] = Field(None, description="Digital signature for integrity verification")
    
    @validator('version')
    def validate_version(cls, v):
        """Ensure version is 0.2"""
        if v != "0.2":
            raise ValueError("PromatraHandshake version must be 0.2")
        return v
    
    @validator('attachments')
    def validate_attachments(cls, v):
        """Validate attachment references"""
        if v is not None:
            for attachment in v:
                if not isinstance(attachment, str) or len(attachment.strip()) == 0:
                    raise ValueError("Attachment references must be non-empty strings")
                # Check for valid attachment ID format
                if not attachment.replace('_', '').replace('-', '').isalnum():
                    raise ValueError(f"Invalid attachment ID format: {attachment}")
        return v
    
    @validator('evidence')
    def validate_evidence_consistency(cls, v, values):
        """Validate evidence consistency with attachments"""
        if v is not None and 'attachments' in values and values['attachments'] is not None:
            # Check that attachment references in evidence match declared attachments
            attachment_refs = set(values['attachments'])
            evidence_refs = set()
            
            for evidence in v:
                if evidence.type == EvidenceType.ATTACHMENT_REFERENCE:
                    if 'attachment_id' in evidence.data:
                        evidence_refs.add(evidence.data['attachment_id'])
                
                # Validate content vs attachment_info consistency
                if evidence.content and evidence.attachment_info:
                    try:
                        decoded_content = base64.b64decode(evidence.content)
                        content_size = len(decoded_content)
                        
                        # Check size consistency
                        if evidence.attachment_info.size_bytes != content_size:
                            raise ValueError(f"Content size mismatch for evidence {evidence.id}: "
                                           f"declared {evidence.attachment_info.size_bytes} bytes, "
                                           f"actual {content_size} bytes")
                        
                        # Validate checksum
                        calculated_checksum = hashlib.sha256(decoded_content).hexdigest()
                        if evidence.attachment_info.checksum != calculated_checksum:
                            raise ValueError(f"Content checksum mismatch for evidence {evidence.id}")
                    except Exception as e:
                        raise ValueError(f"Content validation failed for evidence {evidence.id}: {str(e)}")
                
                # Warn if attachment_info exists without content
                if evidence.attachment_info and not evidence.content:
                    # This would typically be logged as a warning in a real implementation
                    pass
            
            # Check for unmatched references
            unmatched_evidence = evidence_refs - attachment_refs
            unmatched_attachments = attachment_refs - evidence_refs
            
            if unmatched_evidence:
                raise ValueError(f"Evidence references non-declared attachments: {unmatched_evidence}")
            
            if unmatched_attachments:
                # Don't fail for this, but would log as warning in real implementation
                pass
        
        return v
    
    @validator('processing_context')
    def validate_processing_context(cls, v):
        """Validate processing context structure"""
        if v is not None:
            required_fields = ['processor_version', 'timestamp']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Missing required processing context field: {field}")
        return v
    
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "version": "0.2",
                "handshake_id": "handshake_001",
                "timestamp": 1672531200.0,
                "attachments": ["attachment_001", "config_schema_v2"],
                "evidence": [
                    {
                        "id": "evidence_001",
                        "type": "marker_weight",
                        "source": "schema_config",
                        "data": {"weight": 0.8, "window": 300},
                        "timestamp": 1672531200.0
                    },
                    {
                        "id": "attachment_ref_001",
                        "type": "attachment_reference",
                        "source": "file_system",
                        "data": {"attachment_id": "attachment_001", "reference_type": "binary_data"},
                        "attachment_info": {
                            "filename": "marker_config.yaml",
                            "content_type": "application/yaml",
                            "size_bytes": 1024,
                            "checksum": "abc123def456...",
                            "encoding": "base64"
                        }
                    }
                ],
                "metadata": {"source": "marker-logic", "format_version": "v0.2"},
                "processing_context": {
                    "processor_version": "2.1.0",
                    "timestamp": 1672531200.0,
                    "environment": "production"
                }
            }
        }


def process_promatra_handshake(handshake_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process PromatraHandshake data with attachment handling"""
    
    result = {
        'valid': False,
        'handshake': None,
        'attachments_processed': [],
        'evidence_processed': [],
        'warnings': [],
        'errors': []
    }
    
    try:
        # Validate the handshake
        validated_handshake = PromatraHandshake(**handshake_data)
        result['valid'] = True
        result['handshake'] = validated_handshake
        
        # Process attachments
        if validated_handshake.attachments:
            for attachment_id in validated_handshake.attachments:
                attachment_result = process_attachment(attachment_id, validated_handshake.evidence)
                result['attachments_processed'].append(attachment_result)
        
        # Process evidence
        if validated_handshake.evidence:
            for evidence in validated_handshake.evidence:
                evidence_result = process_evidence_item(evidence)
                result['evidence_processed'].append(evidence_result)
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(str(e))
    
    return result


def process_attachment(attachment_id: str, evidence_list: Optional[List[Evidence]]) -> Dict[str, Any]:
    """Process individual attachment with enhanced validation and evidence correlation"""
    
    attachment_result = {
        'attachment_id': attachment_id,
        'found_evidence': False,
        'evidence_count': 0,
        'content_available': False,
        'metadata': None,
        'warnings': [],
        'errors': [],
        'integrity_verified': False
    }
    
    if evidence_list:
        related_evidence = []
        
        for evidence in evidence_list:
            # Check for attachment reference evidence
            if evidence.type == EvidenceType.ATTACHMENT_REFERENCE:
                if evidence.data.get('attachment_id') == attachment_id:
                    related_evidence.append(evidence)
                    attachment_result['found_evidence'] = True
                    attachment_result['evidence_count'] += 1
                    
                    if evidence.attachment_info:
                        attachment_result['metadata'] = evidence.attachment_info.dict()
                    
                    if evidence.content:
                        attachment_result['content_available'] = True
                        
                        # Verify content integrity
                        try:
                            decoded_content = base64.b64decode(evidence.content)
                            if evidence.attachment_info:
                                # Verify size
                                if len(decoded_content) == evidence.attachment_info.size_bytes:
                                    # Verify checksum
                                    calculated_checksum = hashlib.sha256(decoded_content).hexdigest()
                                    if calculated_checksum == evidence.attachment_info.checksum:
                                        attachment_result['integrity_verified'] = True
                                    else:
                                        attachment_result['errors'].append("Checksum verification failed")
                                else:
                                    attachment_result['errors'].append("Size mismatch between content and metadata")
                        except Exception as e:
                            attachment_result['errors'].append(f"Content validation error: {str(e)}")
            
            # Check for other evidence types that might reference this attachment
            elif hasattr(evidence, 'data') and isinstance(evidence.data, dict):
                if 'attachment_id' in evidence.data and evidence.data['attachment_id'] == attachment_id:
                    related_evidence.append(evidence)
                    attachment_result['evidence_count'] += 1
        
        # Generate warnings
        if not attachment_result['found_evidence']:
            attachment_result['warnings'].append("No evidence found referencing this attachment")
        
        if attachment_result['content_available'] and not attachment_result['integrity_verified']:
            attachment_result['warnings'].append("Content integrity could not be verified")
        
        # Check for orphaned attachment info without content
        for evidence in related_evidence:
            if evidence.attachment_info and not evidence.content:
                attachment_result['warnings'].append("Attachment metadata present but content is not available")
    
    else:
        attachment_result['warnings'].append("No evidence list provided for correlation")
    
    return attachment_result


def process_evidence_item(evidence: Evidence) -> Dict[str, Any]:
    """Process individual evidence item"""
    
    evidence_result = {
        'evidence_id': evidence.id,
        'type': evidence.type.value,
        'source': evidence.source,
        'has_attachment': evidence.attachment_info is not None,
        'has_content': evidence.content is not None,
        'data_keys': list(evidence.data.keys()) if evidence.data else [],
        'processed_data': {}
    }
    
    # Process specific evidence types
    if evidence.type == EvidenceType.MARKER_WEIGHT:
        evidence_result['processed_data'] = process_marker_weight_evidence(evidence.data)
    elif evidence.type == EvidenceType.SCORING_WINDOW:
        evidence_result['processed_data'] = process_scoring_window_evidence(evidence.data)
    elif evidence.type == EvidenceType.INTUITION_STATE:
        evidence_result['processed_data'] = process_intuition_state_evidence(evidence.data)
    elif evidence.type == EvidenceType.TELEMETRY_DATA:
        evidence_result['processed_data'] = process_telemetry_evidence(evidence.data)
    elif evidence.type == EvidenceType.SCHEMA_CONFIG:
        evidence_result['processed_data'] = process_schema_config_evidence(evidence.data)
    elif evidence.type == EvidenceType.MULTIPLIER_DATA:
        evidence_result['processed_data'] = process_multiplier_data_evidence(evidence.data)
    elif evidence.type == EvidenceType.BINARY_DATA:
        evidence_result['processed_data'] = process_binary_data_evidence(evidence.data)
    elif evidence.type == EvidenceType.ATTACHMENT_REFERENCE:
        evidence_result['processed_data'] = process_attachment_reference_evidence(evidence.data)
    
    return evidence_result


def process_marker_weight_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process marker weight evidence data"""
    
    processed = {
        'weight_value': data.get('weight', 0.0),
        'window_size': data.get('window', 0),
        'marker_id': data.get('marker_id'),
        'confidence': data.get('confidence', 1.0)
    }
    
    # Validate weight range
    if not 0.0 <= processed['weight_value'] <= 1.0:
        processed['warning'] = f"Weight value {processed['weight_value']} outside normal range [0.0, 1.0]"
    
    return processed


def process_scoring_window_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process scoring window evidence data"""
    
    processed = {
        'window_start': data.get('start_time'),
        'window_end': data.get('end_time'),
        'window_duration': data.get('duration'),
        'score_type': data.get('score_type'),
        'threshold_values': data.get('thresholds', {})
    }
    
    return processed


def process_intuition_state_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process intuition state evidence data"""
    
    processed = {
        'state': data.get('state', 'unknown'),  # provisional, confirmed, decayed
        'multiplier': data.get('multiplier', 1.0),
        'confidence': data.get('confidence', 0.0),
        'transition_timestamp': data.get('transition_timestamp'),
        'telemetry': data.get('telemetry', {})
    }
    
    # Validate state values
    valid_states = ['provisional', 'confirmed', 'decayed']
    if processed['state'] not in valid_states:
        processed['warning'] = f"Invalid intuition state: {processed['state']}"
    
    return processed


def process_telemetry_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process telemetry evidence data"""
    
    processed = {
        'metrics': data.get('metrics', {}),
        'performance_data': data.get('performance', {}),
        'error_counts': data.get('errors', {}),
        'timestamp_range': data.get('time_range', {})
    }
    
    return processed


def process_schema_config_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process schema configuration evidence data"""
    
    processed = {
        'schema_version': data.get('schema_version'),
        'config_type': data.get('config_type'),
        'validation_rules': data.get('validation_rules', {}),
        'field_mappings': data.get('field_mappings', {}),
        'constraints': data.get('constraints', {})
    }
    
    # Validate schema version format
    if processed['schema_version']:
        try:
            version_parts = processed['schema_version'].split('.')
            if len(version_parts) < 2:
                processed['warning'] = f"Invalid schema version format: {processed['schema_version']}"
        except Exception:
            processed['warning'] = "Failed to parse schema version"
    
    return processed


def process_multiplier_data_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process multiplier data evidence"""
    
    processed = {
        'multiplier_id': data.get('multiplier_id'),
        'base_value': data.get('base_value', 1.0),
        'adjustment_factor': data.get('adjustment_factor', 1.0),
        'final_multiplier': data.get('final_multiplier'),
        'calculation_method': data.get('calculation_method'),
        'context_factors': data.get('context_factors', {})
    }
    
    # Calculate final multiplier if not provided
    if processed['final_multiplier'] is None:
        processed['final_multiplier'] = processed['base_value'] * processed['adjustment_factor']
    
    # Validate multiplier ranges
    if processed['final_multiplier'] < 0:
        processed['warning'] = f"Negative multiplier detected: {processed['final_multiplier']}"
    elif processed['final_multiplier'] > 10:
        processed['warning'] = f"Very high multiplier detected: {processed['final_multiplier']}"
    
    return processed


def process_binary_data_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process binary data evidence"""
    
    processed = {
        'data_type': data.get('data_type'),
        'encoding': data.get('encoding', 'base64'),
        'size_bytes': data.get('size_bytes'),
        'checksum': data.get('checksum'),
        'mime_type': data.get('mime_type'),
        'compression': data.get('compression')
    }
    
    # Validate encoding type
    supported_encodings = ['base64', 'hex', 'raw']
    if processed['encoding'] not in supported_encodings:
        processed['warning'] = f"Unsupported encoding: {processed['encoding']}"
    
    # Check size limits
    if processed['size_bytes'] and processed['size_bytes'] > 10 * 1024 * 1024:  # 10MB limit
        processed['warning'] = f"Large binary data detected: {processed['size_bytes']} bytes"
    
    return processed


def process_attachment_reference_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process attachment reference evidence"""
    
    processed = {
        'attachment_id': data.get('attachment_id'),
        'reference_type': data.get('reference_type'),
        'access_method': data.get('access_method'),
        'file_path': data.get('file_path'),
        'url': data.get('url'),
        'inline_content': data.get('inline_content', False)
    }
    
    # Validate attachment ID format
    if processed['attachment_id']:
        if not processed['attachment_id'].replace('_', '').replace('-', '').isalnum():
            processed['warning'] = f"Invalid attachment ID format: {processed['attachment_id']}"
    
    # Check access method consistency
    if processed['file_path'] and processed['url']:
        processed['warning'] = "Both file_path and url specified - ambiguous access method"
    
    return processed