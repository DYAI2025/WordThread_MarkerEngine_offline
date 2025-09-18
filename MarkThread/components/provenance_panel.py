"""
WordThread Marker-Engine Provenance Panel
Comprehensive audit trail and data lineage tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

def render_provenance_panel():
    """Main provenance panel with comprehensive audit trail display"""
    
    # WordThread branding header with orange gradient
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #FF4500, #FFD700);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(255, 69, 0, 0.3);
    ">
        <h2 style="color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            🔍 Provenance & Audit Trail
        </h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Complete data lineage tracking from upload through analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show demo mode banner if using synthetic data
    if getattr(st.session_state, 'using_synthetic_data', False):
        st.warning("🧪 **Demo Mode**: Showing synthetic provenance data for demonstration. Upload real data to see actual audit trails.")
    
    # Tabbed interface for different provenance views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview", 
        "📂 Data Sources", 
        "⚙️ Processing History", 
        "🔄 Transformations", 
        "📊 Export Trail"
    ])
    
    with tab1:
        render_provenance_overview()
    
    with tab2:
        render_data_sources_lineage()
    
    with tab3:
        render_processing_history()
    
    with tab4:
        render_transformation_pipeline()
    
    with tab5:
        render_export_audit_trail()


def render_provenance_overview():
    """Render high-level provenance overview"""
    
    st.markdown("#### 📋 Provenance Overview")
    
    # Collect all provenance data
    provenance_data = collect_provenance_data()
    
    if not provenance_data:
        st.info("No provenance data available. Upload data to begin tracking audit trails.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Data Sources",
            len(provenance_data.get('sources', [])),
            help="Number of distinct data sources processed"
        )
    
    with col2:
        st.metric(
            "Processing Steps",
            len(provenance_data.get('processing_steps', [])),
            help="Total number of processing operations performed"
        )
    
    with col3:
        total_records = sum(s.get('record_count', 0) for s in provenance_data.get('sources', []))
        st.metric(
            "Total Records",
            f"{total_records:,}",
            help="Total number of records processed across all sources"
        )
    
    with col4:
        st.metric(
            "Data Quality",
            f"{provenance_data.get('quality_score', 0):.1%}",
            help="Overall data quality score based on validation results"
        )
    
    # Data lineage flow diagram
    render_lineage_flow_diagram(provenance_data)
    
    # Recent activity timeline
    render_recent_activity_timeline(provenance_data)


def render_data_sources_lineage():
    """Render detailed data sources and lineage information"""
    
    st.markdown("#### 📂 Data Sources Lineage")
    
    provenance_data = collect_provenance_data()
    sources = provenance_data.get('sources', [])
    
    if not sources:
        st.info("No data sources tracked yet. Upload files to begin tracking lineage.")
        return
    
    # Sources filter
    source_filter = st.selectbox(
        "Filter by Source Type",
        ["All Sources", "AnalysisBundle JSON", "SQLite Database", "PromatraHandshake"],
        key="source_filter"
    )
    
    # Display sources
    for i, source in enumerate(sources):
        if source_filter != "All Sources" and source.get('type') != source_filter.replace(" ", ""):
            continue
            
        with st.expander(f"📊 {source.get('name', f'Source {i+1}')} - {source.get('type', 'Unknown')}", expanded=i==0):
            
            # Source metadata
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Source Information:**")
                st.write(f"• **Type:** {source.get('type', 'Unknown')}")
                st.write(f"• **Upload Time:** {source.get('upload_time', 'Unknown')}")
                st.write(f"• **File Size:** {format_file_size(source.get('file_size', 0))}")
                st.write(f"• **Record Count:** {source.get('record_count', 0):,}")
            
            with col2:
                st.markdown("**Data Quality:**")
                st.write(f"• **Validation Status:** {'✅ Passed' if source.get('validation_passed') else '❌ Failed'}")
                st.write(f"• **Schema Compliance:** {'✅ Valid' if source.get('schema_valid') else '❌ Invalid'}")
                st.write(f"• **Missing Fields:** {len(source.get('missing_fields', []))}")
                st.write(f"• **Warnings:** {len(source.get('warnings', []))}")
            
            # Detailed metadata
            if source.get('metadata'):
                st.markdown("**Source Metadata:**")
                st.json(source['metadata'])
            
            # Schema information
            if source.get('schema'):
                st.markdown("**Schema Information:**")
                render_schema_table(source['schema'])


def render_processing_history():
    """Render detailed processing history and operations"""
    
    st.markdown("#### ⚙️ Processing History")
    
    provenance_data = collect_provenance_data()
    processing_steps = provenance_data.get('processing_steps', [])
    
    if not processing_steps:
        st.info("No processing history available. Data processing will be tracked here.")
        return
    
    # Time range filter
    col1, col2 = st.columns(2)
    
    with col1:
        time_filter = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week", "All Time"],
            key="processing_time_filter"
        )
    
    with col2:
        operation_filter = st.selectbox(
            "Operation Type",
            ["All Operations", "Data Upload", "Validation", "Processing", "Analysis", "Export"],
            key="operation_filter"
        )
    
    # Filter processing steps
    filtered_steps = filter_processing_steps(processing_steps, time_filter, operation_filter)
    
    # Processing timeline
    if filtered_steps:
        st.markdown("**📈 Processing Timeline:**")
        render_processing_timeline(filtered_steps)
    
    # Detailed processing log
    st.markdown("**📋 Detailed Processing Log:**")
    
    for step in reversed(filtered_steps):  # Most recent first
        
        # Color code by operation type
        color_map = {
            "Data Upload": "#4CAF50",
            "Validation": "#2196F3", 
            "Processing": "#FF9800",
            "Analysis": "#9C27B0",
            "Export": "#607D8B"
        }
        
        operation_color = color_map.get(step.get('operation_type', 'Processing'), "#607D8B")
        
        with st.container():
            st.markdown(f"""
            <div style="
                border-left: 4px solid {operation_color};
                padding: 1rem;
                margin: 0.5rem 0;
                background: rgba(255,255,255,0.05);
                border-radius: 0 5px 5px 0;
            ">
                <strong style="color: {operation_color};">{step.get('operation_type', 'Processing')}</strong>
                - {step.get('description', 'Unknown operation')}
                <br><small>🕒 {step.get('timestamp', 'Unknown time')} | 
                ⏱️ Duration: {step.get('duration', 'Unknown')} | 
                📊 Status: {step.get('status', 'Unknown')}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Show details if available
            if step.get('details'):
                with st.expander("View Details"):
                    st.json(step['details'])


def render_transformation_pipeline():
    """Render data transformation pipeline visualization"""
    
    st.markdown("#### 🔄 Data Transformation Pipeline")
    
    provenance_data = collect_provenance_data()
    transformations = provenance_data.get('transformations', [])
    
    if not transformations:
        st.info("No data transformations tracked yet. Processing operations will appear here.")
        return
    
    # Pipeline visualization
    st.markdown("**🔄 Transformation Flow:**")
    render_transformation_flow(transformations)
    
    # Transformation details
    st.markdown("**📋 Transformation Details:**")
    
    for i, transform in enumerate(transformations):
        with st.expander(f"Step {i+1}: {transform.get('name', 'Transformation')}"):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Input:**")
                st.write(f"• **Records:** {transform.get('input_records', 0):,}")
                st.write(f"• **Columns:** {len(transform.get('input_schema', []))}")
                st.write(f"• **Format:** {transform.get('input_format', 'Unknown')}")
            
            with col2:
                st.markdown("**Output:**")
                st.write(f"• **Records:** {transform.get('output_records', 0):,}")
                st.write(f"• **Columns:** {len(transform.get('output_schema', []))}")
                st.write(f"• **Format:** {transform.get('output_format', 'Unknown')}")
            
            # Transformation logic
            if transform.get('logic'):
                st.markdown("**Transformation Logic:**")
                st.code(transform['logic'], language='python')
            
            # Performance metrics
            if transform.get('performance'):
                st.markdown("**Performance Metrics:**")
                perf = transform['performance']
                st.write(f"• **Processing Time:** {perf.get('duration', 'Unknown')}")
                st.write(f"• **Memory Usage:** {format_memory_size(perf.get('memory_mb', 0))}")
                st.write(f"• **Throughput:** {perf.get('records_per_second', 0):,.0f} records/sec")


def render_export_audit_trail():
    """Render export operations audit trail"""
    
    st.markdown("#### 📊 Export Audit Trail")
    
    provenance_data = collect_provenance_data()
    exports = provenance_data.get('exports', [])
    
    if not exports:
        st.info("No export operations tracked yet. Export activities will be logged here.")
        return
    
    # Export summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Exports", len(exports))
    
    with col2:
        successful_exports = sum(1 for e in exports if e.get('status') == 'success')
        st.metric("Successful", successful_exports)
    
    with col3:
        failed_exports = len(exports) - successful_exports
        st.metric("Failed", failed_exports)
    
    # Export log
    st.markdown("**📋 Export Log:**")
    
    for export in reversed(exports):  # Most recent first
        
        status_color = "#4CAF50" if export.get('status') == 'success' else "#F44336"
        status_icon = "✅" if export.get('status') == 'success' else "❌"
        
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid {status_color};
                padding: 1rem;
                margin: 0.5rem 0;
                background: rgba(255,255,255,0.05);
                border-radius: 5px;
            ">
                <strong>{status_icon} {export.get('export_type', 'Unknown Export')}</strong>
                <br>🕒 {export.get('timestamp', 'Unknown time')}
                <br>📁 Format: {export.get('format', 'Unknown')} | 
                📊 Records: {export.get('record_count', 0):,} | 
                💾 Size: {format_file_size(export.get('file_size', 0))}
            </div>
            """, unsafe_allow_html=True)
            
            # Export details
            if export.get('metadata'):
                with st.expander("Export Metadata"):
                    st.json(export['metadata'])


def collect_provenance_data() -> Dict[str, Any]:
    """Collect all provenance data from various sources"""
    
    provenance_data = {
        'sources': [],
        'processing_steps': [],
        'transformations': [],
        'exports': [],
        'quality_score': 0.0
    }
    
    # Collect from session state
    if hasattr(st.session_state, 'uploaded_data'):
        provenance_data['sources'].extend(extract_source_provenance())
    
    if hasattr(st.session_state, 'processing_history'):
        provenance_data['processing_steps'].extend(st.session_state.processing_history)
    
    if hasattr(st.session_state, 'transformation_history'):
        provenance_data['transformations'].extend(st.session_state.transformation_history)
    
    if hasattr(st.session_state, 'export_history'):
        provenance_data['exports'].extend(st.session_state.export_history)
    
    # Calculate quality score
    provenance_data['quality_score'] = calculate_data_quality_score(provenance_data)
    
    # Add synthetic data if no real data exists
    if not any(provenance_data.values()):
        st.session_state.using_synthetic_data = True
        provenance_data = generate_synthetic_provenance_data()
    
    return provenance_data


def extract_source_provenance() -> List[Dict[str, Any]]:
    """Extract provenance information from uploaded data"""
    
    sources = []
    
    # Check for uploaded files
    for file_type in ['analysis_bundle', 'sqlite_file', 'promatra_handshake']:
        if hasattr(st.session_state, f'{file_type}_data'):
            data = getattr(st.session_state, f'{file_type}_data')
            
            source = {
                'name': data.get('filename', f'{file_type}_data'),
                'type': file_type.replace('_', ' ').title(),
                'upload_time': data.get('upload_time', datetime.now().isoformat()),
                'file_size': data.get('file_size', 0),
                'record_count': data.get('record_count', 0),
                'validation_passed': data.get('validation_passed', True),
                'schema_valid': data.get('schema_valid', True),
                'missing_fields': data.get('missing_fields', []),
                'warnings': data.get('warnings', []),
                'metadata': data.get('metadata', {}),
                'schema': data.get('schema', {})
            }
            
            sources.append(source)
    
    return sources


def render_lineage_flow_diagram(provenance_data: Dict[str, Any]):
    """Render data lineage flow diagram"""
    
    st.markdown("**🔄 Data Lineage Flow:**")
    
    # Simple ASCII flow diagram
    sources = provenance_data.get('sources', [])
    processing_steps = len(provenance_data.get('processing_steps', []))
    exports = len(provenance_data.get('exports', []))
    
    flow_diagram = f"""
    ```
    📂 Data Sources ({len(sources)})
           ⬇️
    ⚙️ Processing Steps ({processing_steps})
           ⬇️
    🔄 Transformations
           ⬇️
    📊 Analysis & Visualization
           ⬇️
    📁 Exports ({exports})
    ```
    """
    
    st.markdown(flow_diagram)


def render_recent_activity_timeline(provenance_data: Dict[str, Any]):
    """Render recent activity timeline"""
    
    st.markdown("**📈 Recent Activity:**")
    
    # Combine all activities
    activities = []
    
    for source in provenance_data.get('sources', []):
        activities.append({
            'timestamp': source.get('upload_time', ''),
            'type': 'Upload',
            'description': f"Uploaded {source.get('name', 'data source')}"
        })
    
    for step in provenance_data.get('processing_steps', []):
        activities.append({
            'timestamp': step.get('timestamp', ''),
            'type': 'Processing',
            'description': step.get('description', 'Processing operation')
        })
    
    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Display recent activities
    for activity in activities[:10]:  # Show last 10 activities
        st.write(f"🕒 {activity.get('timestamp', 'Unknown time')} - **{activity.get('type')}**: {activity.get('description')}")


def render_processing_timeline(processing_steps: List[Dict[str, Any]]):
    """Render processing timeline visualization"""
    
    if not processing_steps:
        return
    
    # Create timeline data
    timeline_data = []
    for step in processing_steps:
        timeline_data.append({
            'Timestamp': step.get('timestamp', ''),
            'Operation': step.get('operation_type', 'Unknown'),
            'Duration': step.get('duration', ''),
            'Status': step.get('status', 'Unknown')
        })
    
    if timeline_data:
        df = pd.DataFrame(timeline_data)
        st.dataframe(df, use_container_width=True)


def render_transformation_flow(transformations: List[Dict[str, Any]]):
    """Render transformation flow visualization"""
    
    flow_text = "```\n"
    for i, transform in enumerate(transformations):
        if i > 0:
            flow_text += "    ⬇️\n"
        flow_text += f"Step {i+1}: {transform.get('name', 'Transform')}\n"
        flow_text += f"  Input: {transform.get('input_records', 0):,} records\n"
        flow_text += f"  Output: {transform.get('output_records', 0):,} records\n"
    flow_text += "```"
    
    st.markdown(flow_text)


def render_schema_table(schema: Dict[str, Any]):
    """Render schema information in table format"""
    
    if not schema:
        st.write("No schema information available")
        return
    
    schema_data = []
    for table_name, table_info in schema.items():
        for column in table_info.get('columns', []):
            schema_data.append({
                'Table': table_name,
                'Column': column.get('name', ''),
                'Type': column.get('type', ''),
                'Required': column.get('required', False)
            })
    
    if schema_data:
        df = pd.DataFrame(schema_data)
        st.dataframe(df, use_container_width=True)


def filter_processing_steps(steps: List[Dict[str, Any]], time_filter: str, operation_filter: str) -> List[Dict[str, Any]]:
    """Filter processing steps based on time and operation filters"""
    
    filtered_steps = steps.copy()
    
    # Time filtering
    if time_filter != "All Time":
        cutoff_time = datetime.now()
        if time_filter == "Last Hour":
            cutoff_time -= timedelta(hours=1)
        elif time_filter == "Last 6 Hours":
            cutoff_time -= timedelta(hours=6)
        elif time_filter == "Last 24 Hours":
            cutoff_time -= timedelta(hours=24)
        elif time_filter == "Last Week":
            cutoff_time -= timedelta(days=7)
        
        # Filter steps (this is simplified - in real implementation would parse timestamps)
        # For now, keep all steps
    
    # Operation filtering
    if operation_filter != "All Operations":
        filtered_steps = [s for s in filtered_steps if s.get('operation_type') == operation_filter]
    
    return filtered_steps


def calculate_data_quality_score(provenance_data: Dict[str, Any]) -> float:
    """Calculate overall data quality score"""
    
    sources = provenance_data.get('sources', [])
    if not sources:
        return 0.0
    
    # Simple quality scoring based on validation results
    quality_scores = []
    for source in sources:
        score = 1.0
        if not source.get('validation_passed', True):
            score -= 0.5
        if not source.get('schema_valid', True):
            score -= 0.3
        if source.get('warnings', []):
            score -= 0.1 * min(len(source['warnings']), 2)
        
        quality_scores.append(max(0.0, score))
    
    return sum(quality_scores) / len(quality_scores)


def generate_synthetic_provenance_data() -> Dict[str, Any]:
    """Generate synthetic provenance data for demonstration"""
    
    return {
        'sources': [
            {
                'name': 'sample_analysis_bundle.json',
                'type': 'AnalysisBundle',
                'upload_time': (datetime.now() - timedelta(hours=2)).isoformat(),
                'file_size': 2048576,
                'record_count': 15420,
                'validation_passed': True,
                'schema_valid': True,
                'missing_fields': [],
                'warnings': ['Minor timestamp formatting inconsistency'],
                'metadata': {'version': '1.0', 'source': 'wordthread_engine'},
                'schema': {'hits': {'columns': [{'name': 'id', 'type': 'int'}, {'name': 'marker_id', 'type': 'string'}]}}
            },
            {
                'name': 'marker_data.sqlite',
                'type': 'SQLite Database', 
                'upload_time': (datetime.now() - timedelta(hours=1)).isoformat(),
                'file_size': 5242880,
                'record_count': 28350,
                'validation_passed': True,
                'schema_valid': True,
                'missing_fields': [],
                'warnings': [],
                'metadata': {'tables': 4, 'indexes': 6},
                'schema': {'hits': {'columns': [{'name': 'id', 'type': 'int'}, {'name': 'ts', 'type': 'timestamp'}]}}
            }
        ],
        'processing_steps': [
            {
                'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'operation_type': 'Data Upload',
                'description': 'Uploaded and validated AnalysisBundle JSON',
                'duration': '2.3s',
                'status': 'success',
                'details': {'validation_checks': 12, 'warnings': 1}
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'operation_type': 'Processing',
                'description': 'Applied LTTB downsampling to large dataset',
                'duration': '8.7s',
                'status': 'success',
                'details': {'original_size': 28350, 'downsampled_size': 5000}
            }
        ],
        'transformations': [
            {
                'name': 'LTTB Downsampling',
                'input_records': 28350,
                'output_records': 5000,
                'input_schema': ['id', 'marker_id', 'ts', 'payload'],
                'output_schema': ['id', 'marker_id', 'ts', 'payload'],
                'input_format': 'SQLite',
                'output_format': 'Pandas DataFrame',
                'logic': 'Largest-Triangle-Three-Buckets algorithm for time series downsampling',
                'performance': {'duration': '8.7s', 'memory_mb': 45, 'records_per_second': 3256}
            }
        ],
        'exports': [
            {
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'export_type': 'Analysis Summary',
                'format': 'JSON',
                'status': 'success',
                'record_count': 5000,
                'file_size': 1024000,
                'metadata': {'includes_visualizations': True, 'compression': 'gzip'}
            }
        ],
        'quality_score': 0.92
    }


# Utility functions
def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_memory_size(memory_mb: float) -> str:
    """Format memory size in human readable format"""
    if memory_mb < 1024:
        return f"{memory_mb:.1f} MB"
    else:
        return f"{memory_mb/1024:.1f} GB"