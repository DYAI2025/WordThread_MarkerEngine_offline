import streamlit as st
from schemas.analysis_bundle import AnalysisBundle, validate_marker_architecture
from schemas.promatra_handshake import PromatraHandshake, process_promatra_handshake
from pydantic import ValidationError
import json
from typing import Dict, Any

def validate_analysis_bundle(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate AnalysisBundle using Pydantic schema"""
    validation_result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'data': None,
        'architecture_validation': None
    }
    
    try:
        # Primary schema validation
        validated_bundle = AnalysisBundle(**data)
        validation_result['valid'] = True
        validation_result['data'] = validated_bundle
        
        # Architecture validation
        arch_validation = validate_marker_architecture(validated_bundle.hits)
        validation_result['architecture_validation'] = arch_validation
        validation_result['warnings'].extend(arch_validation['warnings'])
        
        # Additional business logic validations
        business_validation = perform_business_validations(validated_bundle)
        validation_result['warnings'].extend(business_validation.get('warnings', []))
        
    except ValidationError as e:
        validation_result['valid'] = False
        validation_result['errors'] = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'] = [f"Unexpected validation error: {str(e)}"]
    
    return validation_result

def validate_promatra_handshake(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate PromatraHandshake v0.2 with enhanced attachment processing"""
    validation_result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'data': None,
        'attachment_processing': None,
        'evidence_processing': None
    }
    
    try:
        # Use enhanced processing function
        processing_result = process_promatra_handshake(data)
        
        validation_result['valid'] = processing_result['valid']
        validation_result['data'] = processing_result['handshake']
        validation_result['errors'] = processing_result.get('errors', [])
        validation_result['warnings'] = processing_result.get('warnings', [])
        validation_result['attachment_processing'] = processing_result.get('attachments_processed', [])
        validation_result['evidence_processing'] = processing_result.get('evidence_processed', [])
        
        # Add additional warnings for enhanced features
        if processing_result['valid'] and processing_result['handshake']:
            handshake = processing_result['handshake']
            
            # Check for v0.2 specific features
            if handshake.processing_context:
                validation_result['warnings'].append("Enhanced v0.2 processing context detected")
            
            if handshake.signature:
                validation_result['warnings'].append("Digital signature present - integrity verification available")
            
            # Check evidence types
            if handshake.evidence:
                evidence_types = set(evidence.type.value for evidence in handshake.evidence)
                if 'intuition_state' in evidence_types:
                    validation_result['warnings'].append("Intuition state evidence detected - advanced CLU processing available")
                
                if 'telemetry_data' in evidence_types:
                    validation_result['warnings'].append("Telemetry data present - performance monitoring data available")
        
    except ValidationError as e:
        validation_result['valid'] = False
        validation_result['errors'] = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'] = [f"Unexpected validation error: {str(e)}"]
    
    return validation_result

def validate_sqlite_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate SQLite data structure"""
    validation_result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'data': data
    }
    
    try:
        required_tables = ['messages', 'hits']  # Minimum required tables
        
        if 'tables' not in data:
            validation_result['errors'].append("No table information found in SQLite data")
            return validation_result
        
        available_tables = list(data['tables'].keys())
        missing_tables = [table for table in required_tables if table not in available_tables]
        
        if missing_tables:
            validation_result['warnings'].append(f"Recommended tables missing: {missing_tables}")
        
        # Validate hits table structure if present
        if 'hits' in data['tables']:
            hits_data = data['tables']['hits']
            if not hits_data:
                validation_result['warnings'].append("Hits table is empty")
            else:
                # Check for required columns
                required_columns = ['id', 'marker_id', 'ts']
                if hits_data:
                    available_columns = list(hits_data[0].keys()) if hits_data else []
                    missing_columns = [col for col in required_columns if col not in available_columns]
                    
                    if missing_columns:
                        validation_result['errors'].append(f"Missing required columns in hits table: {missing_columns}")
                    else:
                        validation_result['valid'] = True
        else:
            validation_result['valid'] = True  # Allow without hits table but warn
            validation_result['warnings'].append("No hits table found - limited analysis capabilities")
        
        # Additional table validations
        table_validations = validate_optional_tables(data['tables'])
        validation_result['warnings'].extend(table_validations.get('warnings', []))
        
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'] = [f"SQLite validation error: {str(e)}"]
    
    return validation_result

def perform_business_validations(bundle: AnalysisBundle) -> Dict[str, Any]:
    """Perform business logic validations on AnalysisBundle"""
    validation_result = {
        'warnings': [],
        'recommendations': []
    }
    
    # Check hit distribution
    if len(bundle.hits) == 0:
        validation_result['warnings'].append("No hits found in bundle")
    elif len(bundle.hits) < 5:
        validation_result['warnings'].append("Very few hits found - analysis may be limited")
    
    # Check time span
    if bundle.hits:
        timestamps = [hit.ts for hit in bundle.hits]
        time_span = max(timestamps) - min(timestamps)
        
        if time_span < 60:  # Less than 1 minute
            validation_result['warnings'].append("Short time span detected - limited temporal analysis")
        elif time_span > 86400 * 30:  # More than 30 days
            validation_result['recommendations'].append("Long time span detected - consider time-based filtering")
    
    # Check conversation distribution
    conversations = set(hit.conv for hit in bundle.hits if hit.conv)
    if len(conversations) == 0:
        validation_result['warnings'].append("No conversation identifiers found")
    elif len(conversations) == 1:
        validation_result['warnings'].append("Single conversation detected - limited cross-conversation analysis")
    
    # Check marker diversity
    marker_ids = set(hit.marker_id for hit in bundle.hits)
    if len(marker_ids) < 3:
        validation_result['warnings'].append("Limited marker diversity detected")
    
    return validation_result

def validate_optional_tables(tables: Dict[str, Any]) -> Dict[str, Any]:
    """Validate optional SQLite tables"""
    validation_result = {
        'warnings': [],
        'info': []
    }
    
    # Check for additional useful tables
    optional_tables = {
        'aggregates': 'Aggregate data available for enhanced analysis',
        'scores': 'Scoring data available for confidence metrics',
        'drift_axes': 'Drift analysis data available',
        'provenance': 'Data provenance information available'
    }
    
    for table_name, info_message in optional_tables.items():
        if table_name in tables:
            validation_result['info'].append(info_message)
        else:
            validation_result['warnings'].append(f"Optional table '{table_name}' not found")
    
    return validation_result

def display_validation_results(validation_result: Dict[str, Any], title: str = "Validation Results"):
    """Display validation results in Streamlit UI"""
    st.markdown(f"### {title}")
    
    if validation_result['valid']:
        st.success("✅ Validation successful!")
        
        # Show architecture stats if available
        if 'architecture_validation' in validation_result and validation_result['architecture_validation']:
            arch_stats = validation_result['architecture_validation']['architecture_stats']
            st.markdown("#### 🏗️ Marker Architecture")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ATO Markers", arch_stats.get('ATO', 0))
            with col2:
                st.metric("SEM Markers", arch_stats.get('SEM', 0))
            with col3:
                st.metric("CLU Markers", arch_stats.get('CLU', 0))
            with col4:
                st.metric("MEMA Markers", arch_stats.get('MEMA', 0))
    else:
        st.error("❌ Validation failed!")
        
        if validation_result['errors']:
            st.markdown("#### Errors:")
            for error in validation_result['errors']:
                st.error(f"• {error}")
    
    # Show warnings
    if validation_result.get('warnings'):
        st.markdown("#### ⚠️ Warnings:")
        for warning in validation_result['warnings']:
            st.warning(f"• {warning}")
    
    # Show info/recommendations
    if validation_result.get('recommendations'):
        st.markdown("#### 💡 Recommendations:")
        for rec in validation_result['recommendations']:
            st.info(f"• {rec}")
