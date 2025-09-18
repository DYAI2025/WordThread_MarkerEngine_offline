import streamlit as st
import json
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import os

# Import custom components
from components.file_upload import render_file_upload
from components.data_validation import validate_analysis_bundle, validate_sqlite_data, validate_promatra_handshake
from components.charts import render_charts
from components.markers_table import render_markers_table
from components.advanced_drift_panel import render_advanced_drift_panel
from components.evidence_panel import render_evidence_panel
from components.export_utils import export_png, export_json
from components.performance_dashboard import render_performance_dashboard
from components.provenance_panel import render_provenance_panel
from components.file_monitor import render_file_monitor_panel
from components.intuitions_panel import render_intuitions_panel
from utils.data_processing import process_analysis_bundle, process_sqlite_data
from utils.sqlite_handler import SQLiteHandler

# Custom CSS for WordThread branding
def load_custom_css():
    with open("assets/styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'sqlite_data' not in st.session_state:
        st.session_state.sqlite_data = None
    if 'selected_markers' not in st.session_state:
        st.session_state.selected_markers = []
    if 'time_filter' not in st.session_state:
        st.session_state.time_filter = None
    if 'current_view_state' not in st.session_state:
        st.session_state.current_view_state = {}
    if 'promatra_handshake' not in st.session_state:
        st.session_state.promatra_handshake = None

def main():
    # Set page configuration
    st.set_page_config(
        page_title="WordThread Marker-Engine Frontend",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Main header with WordThread branding
    st.markdown("""
    <div class="wordthread-header">
        <h1 class="wordthread-title">WordThread</h1>
        <p class="wordthread-subtitle">Marker-Engine Frontend</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for file upload and controls
    with st.sidebar:
        st.markdown("### 📁 Data Ingestion")
        uploaded_files = render_file_upload()
        
        if uploaded_files:
            process_uploaded_files(uploaded_files)
        
        # Additional controls
        if st.session_state.data_loaded:
            st.markdown("### ⚙️ Controls")
            
            # Time range filter
            st.markdown("#### Time Filter")
            if st.session_state.analysis_data and 'hits' in st.session_state.analysis_data:
                hits_df = pd.DataFrame(st.session_state.analysis_data['hits'])
                if 'ts' in hits_df.columns and len(hits_df) > 0:
                    min_time = pd.to_datetime(hits_df['ts'].min(), unit='s')
                    max_time = pd.to_datetime(hits_df['ts'].max(), unit='s')
                    
                    time_range = st.date_input(
                        "Select time range",
                        value=(min_time.date(), max_time.date()),
                        min_value=min_time.date(),
                        max_value=max_time.date()
                    )
                    st.session_state.time_filter = time_range
            
            # Export controls
            st.markdown("### 📤 Export")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Export PNG"):
                    export_png_data()
            
            with col2:
                if st.button("📋 Export JSON"):
                    export_json_data()
    
    # Main content area
    if not st.session_state.data_loaded:
        render_welcome_screen()
    
    # Always show main dashboard to provide access to all tabs
    render_main_dashboard()

def render_promatra_handshake_panel():
    """Render PromatraHandshake analysis panel"""
    
    if not st.session_state.promatra_handshake:
        st.info("🤝 No PromatraHandshake data loaded. Upload a PromatraHandshake v0.2 JSON file to see detailed analysis.")
        
        # Show example format
        with st.expander("📄 PromatraHandshake v0.2 Format Example"):
            example_format = {
                "version": "0.2",
                "handshake_id": "handshake_001",
                "timestamp": 1672531200.0,
                "attachments": ["attachment_001"],
                "evidence": [
                    {
                        "id": "evidence_001",
                        "type": "marker_weight",
                        "source": "schema_config",
                        "data": {"weight": 0.8, "window": 300}
                    }
                ],
                "metadata": {"source": "marker-logic"}
            }
            st.json(example_format)
        
        return
    
    handshake_data = st.session_state.promatra_handshake
    
    # Handshake overview
    st.markdown("### 🤝 PromatraHandshake v0.2 Analysis")
    
    # Basic information
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Handshake ID", handshake_data['data'].handshake_id if handshake_data['data'] else "N/A")
    
    with col2:
        attachment_count = len(handshake_data.get('attachment_processing', []))
        st.metric("Attachments", attachment_count)
    
    with col3:
        evidence_count = len(handshake_data.get('evidence_processing', []))
        st.metric("Evidence Items", evidence_count)
    
    with col4:
        warning_count = len(handshake_data.get('warnings', []))
        st.metric("Warnings", warning_count)
    
    # Show warnings and errors
    if handshake_data.get('warnings'):
        st.warning("⚠️ Warnings detected")
        for warning in handshake_data['warnings']:
            st.write(f"• {warning}")
    
    if handshake_data.get('errors'):
        st.error("❌ Errors detected")
        for error in handshake_data['errors']:
            st.write(f"• {error}")
    
    # Detailed analysis tabs
    tab1, tab2, tab3 = st.tabs(["📁 Attachments", "🔍 Evidence", "📊 Metadata"])
    
    with tab1:
        render_attachment_analysis(handshake_data.get('attachment_processing', []))
    
    with tab2:
        render_evidence_analysis(handshake_data.get('evidence_processing', []))
    
    with tab3:
        render_metadata_analysis(handshake_data['data'] if handshake_data['data'] else None)

def render_attachment_analysis(attachment_data):
    """Render detailed attachment analysis"""
    
    if not attachment_data:
        st.info("No attachment data to display.")
        return
    
    st.markdown("#### 📁 Attachment Processing Results")
    
    for attachment in attachment_data:
        with st.expander(f"Attachment: {attachment['attachment_id']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Status:**")
                if attachment['found_evidence']:
                    st.success("✅ Evidence found")
                else:
                    st.warning("⚠️ No evidence found")
                
                st.metric("Evidence Count", attachment['evidence_count'])
                
                if attachment['content_available']:
                    st.success("📎 Content available")
                else:
                    st.info("📄 Content not available")
            
            with col2:
                if attachment.get('metadata'):
                    st.markdown("**Metadata:**")
                    st.json(attachment['metadata'])
                
                if attachment.get('warnings'):
                    st.markdown("**Warnings:**")
                    for warning in attachment['warnings']:
                        st.warning(f"• {warning}")
                
                if attachment.get('errors'):
                    st.markdown("**Errors:**")
                    for error in attachment['errors']:
                        st.error(f"• {error}")
                
                if attachment.get('integrity_verified'):
                    st.success("✓ Integrity verified")
                elif attachment['content_available']:
                    st.warning("⚠️ Integrity not verified")

def render_evidence_analysis(evidence_data):
    """Render detailed evidence analysis"""
    
    if not evidence_data:
        st.info("No evidence data to display.")
        return
    
    st.markdown("#### 🔍 Evidence Processing Results")
    
    # Evidence type summary
    evidence_types = {}
    for evidence in evidence_data:
        evidence_type = evidence['type']
        if evidence_type not in evidence_types:
            evidence_types[evidence_type] = 0
        evidence_types[evidence_type] += 1
    
    st.markdown("**Evidence Type Distribution:**")
    for evidence_type, count in evidence_types.items():
        st.write(f"• {evidence_type}: {count} items")
    
    # Detailed evidence items
    for evidence in evidence_data:
        with st.expander(f"Evidence: {evidence['evidence_id']} ({evidence['type']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Type:** {evidence['type']}")
                st.markdown(f"**Source:** {evidence['source']}")
                
                if evidence['has_attachment']:
                    st.success("📎 Has attachment info")
                
                if evidence['has_content']:
                    st.success("📎 Has content")
                
                if evidence['data_keys']:
                    st.markdown(f"**Data keys:** {', '.join(evidence['data_keys'])}")
            
            with col2:
                if evidence['processed_data']:
                    st.markdown("**Processed Data:**")
                    st.json(evidence['processed_data'])

def render_metadata_analysis(handshake_obj):
    """Render metadata analysis"""
    
    if not handshake_obj:
        st.info("No handshake metadata to display.")
        return
    
    st.markdown("#### 📊 Handshake Metadata")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Basic Information:**")
        st.write(f"Version: {handshake_obj.version}")
        st.write(f"Handshake ID: {handshake_obj.handshake_id}")
        st.write(f"Timestamp: {handshake_obj.timestamp}")
        
        if handshake_obj.attachments:
            st.markdown("**Declared Attachments:**")
            for attachment in handshake_obj.attachments:
                st.write(f"• {attachment}")
    
    with col2:
        if handshake_obj.metadata:
            st.markdown("**Metadata:**")
            st.json(handshake_obj.metadata.dict() if hasattr(handshake_obj.metadata, 'dict') else handshake_obj.metadata)
        
        if handshake_obj.processing_context:
            st.markdown("**Processing Context:**")
            st.json(handshake_obj.processing_context.dict() if hasattr(handshake_obj.processing_context, 'dict') else handshake_obj.processing_context)
        
        if handshake_obj.signature:
            st.markdown("**Digital Signature:**")
            st.code(handshake_obj.signature[:64] + "..." if len(handshake_obj.signature) > 64 else handshake_obj.signature)

def process_uploaded_files(files):
    """Process uploaded files and validate data"""
    try:
        for file in files:
            if file.name.endswith('.json'):
                # Process JSON AnalysisBundle
                content = json.loads(file.getvalue().decode('utf-8'))
                
                # Determine file type and validate accordingly
                if 'bundle_version' in content:
                    # AnalysisBundle detected
                    validation_result = validate_analysis_bundle(content)
                    
                    if validation_result['valid']:
                        st.session_state.analysis_data = process_analysis_bundle(content)
                        st.session_state.data_loaded = True
                        st.success(f"✅ Successfully loaded and validated AnalysisBundle from {file.name}")
                    else:
                        st.error(f"❌ AnalysisBundle validation failed for {file.name}: {validation_result['errors']}")
                        
                elif 'version' in content and content.get('version') == '0.2' and 'handshake_id' in content:
                    # PromatraHandshake v0.2 detected
                    validation_result = validate_promatra_handshake(content)
                    
                    if validation_result['valid']:
                        st.session_state.promatra_handshake = validation_result
                        st.session_state.data_loaded = True
                        st.success(f"✅ Successfully loaded and validated PromatraHandshake v0.2 from {file.name}")
                        
                        # Show processing summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            attachment_count = len(validation_result.get('attachment_processing', []))
                            st.metric("Attachments Processed", attachment_count)
                        
                        with col2:
                            evidence_count = len(validation_result.get('evidence_processing', []))
                            st.metric("Evidence Items", evidence_count)
                        
                        with col3:
                            warning_count = len(validation_result.get('warnings', []))
                            st.metric("Warnings", warning_count)
                    else:
                        st.error(f"❌ PromatraHandshake validation failed for {file.name}: {validation_result['errors']}")
                        
                else:
                    st.error(f"❌ Unknown JSON format in {file.name}. Expected AnalysisBundle or PromatraHandshake v0.2.")
                    
            elif file.name.endswith('.sqlite') or file.name.endswith('.db'):
                # Process SQLite file
                with open(f"temp_{file.name}", "wb") as f:
                    f.write(file.getvalue())
                
                try:
                    sqlite_handler = SQLiteHandler(f"temp_{file.name}")
                    sqlite_data = sqlite_handler.extract_data()
                    
                    validation_result = validate_sqlite_data(sqlite_data)
                    
                    if validation_result['valid']:
                        st.session_state.sqlite_data = process_sqlite_data(sqlite_data)
                        st.session_state.data_loaded = True
                        st.success(f"✅ Successfully loaded SQLite data from {file.name}")
                    else:
                        st.error(f"❌ SQLite validation failed for {file.name}: {validation_result['errors']}")
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(f"temp_{file.name}"):
                        os.remove(f"temp_{file.name}")
        
        # Update view state
        update_view_state()
        
    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")

def render_welcome_screen():
    """Render welcome screen when no data is loaded"""
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-content">
            <h2>🔬 Welcome to WordThread Marker-Engine</h2>
            <p>Upload your AnalysisBundle JSON or SQLite files to begin analyzing marker data.</p>
            
            <div class="feature-grid">
                <div class="feature-item">
                    <h3>📊 Interactive Charts</h3>
                    <p>Visualize marker patterns with line charts and heatmaps</p>
                </div>
                <div class="feature-item">
                    <h3>🎯 Marker Analysis</h3>
                    <p>Explore ATO → SEM → CLU → MEMA architecture</p>
                </div>
                <div class="feature-item">
                    <h3>📈 Drift Detection</h3>
                    <p>Monitor temporal changes in marker patterns</p>
                </div>
                <div class="feature-item">
                    <h3>📤 Export Results</h3>
                    <p>Export charts as PNG and view states as JSON</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_main_dashboard():
    """Render the main dashboard with all components"""
    # Top KPIs row
    render_kpis()
    
    # Main content tabs  
    if st.session_state.promatra_handshake:
        # Show PromatraHandshake tab when handshake data is loaded
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["📊 Charts", "🎯 Markers", "📈 Drift Analysis", "🔍 Evidence", "🧠 Intuitions", "⚡ Performance", "🔍 Provenance", "📁 File Monitor", "🤝 PromatraHandshake"])
    else:
        # Standard tabs for AnalysisBundle data
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📊 Charts", "🎯 Markers", "📈 Drift Analysis", "🔍 Evidence", "🧠 Intuitions", "⚡ Performance", "🔍 Provenance", "📁 File Monitor"])
    
    with tab1:
        render_charts(st.session_state.analysis_data, st.session_state.sqlite_data)
    
    with tab2:
        render_markers_table(st.session_state.analysis_data, st.session_state.sqlite_data)
    
    with tab3:
        render_advanced_drift_panel(st.session_state.analysis_data, st.session_state.sqlite_data)
    
    with tab4:
        render_evidence_panel(st.session_state.analysis_data, st.session_state.sqlite_data)
    
    with tab5:
        render_intuitions_panel(st.session_state.analysis_data, st.session_state.sqlite_data)
    
    with tab6:
        render_performance_dashboard()
    
    with tab7:
        render_provenance_panel()
    
    with tab8:
        render_file_monitor_panel()
    
    # Only show PromatraHandshake tab if handshake data is loaded
    if st.session_state.promatra_handshake:
        with tab9:
            render_promatra_handshake_panel()

def render_kpis():
    """Render key performance indicators"""
    st.markdown("### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate KPIs from loaded data
    total_markers = 0
    total_hits = 0
    unique_conversations = 0
    time_span_days = 0
    
    if st.session_state.analysis_data:
        data = st.session_state.analysis_data
        if 'hits' in data:
            hits_df = pd.DataFrame(data['hits'])
            total_hits = len(hits_df)
            if 'marker_id' in hits_df.columns:
                total_markers = hits_df['marker_id'].nunique()
            if 'conv' in hits_df.columns:
                unique_conversations = hits_df['conv'].nunique()
            if 'ts' in hits_df.columns and len(hits_df) > 0:
                min_ts = hits_df['ts'].min()
                max_ts = hits_df['ts'].max()
                time_span_days = (max_ts - min_ts) / 86400  # Convert seconds to days
    
    with col1:
        st.metric("Total Markers", f"{total_markers:,}")
    
    with col2:
        st.metric("Total Hits", f"{total_hits:,}")
    
    with col3:
        st.metric("Conversations", f"{unique_conversations:,}")
    
    with col4:
        st.metric("Time Span (days)", f"{time_span_days:.1f}")

def update_view_state():
    """Update the current view state for export"""
    st.session_state.current_view_state = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'data_loaded': st.session_state.data_loaded,
        'selected_markers': st.session_state.selected_markers,
        'time_filter': str(st.session_state.time_filter) if st.session_state.time_filter else None,
        'has_analysis_data': st.session_state.analysis_data is not None,
        'has_sqlite_data': st.session_state.sqlite_data is not None
    }

def export_png_data():
    """Export current charts as PNG"""
    try:
        png_data = export_png(st.session_state.analysis_data, st.session_state.sqlite_data)
        if png_data:
            st.download_button(
                label="Download PNG Export",
                data=png_data,
                file_name=f"wordthread_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png"
            )
    except Exception as e:
        st.error(f"❌ Error exporting PNG: {str(e)}")

def export_json_data():
    """Export current view state as JSON"""
    try:
        json_data = export_json(st.session_state.current_view_state)
        st.download_button(
            label="Download JSON Export",
            data=json_data,
            file_name=f"wordthread_state_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    except Exception as e:
        st.error(f"❌ Error exporting JSON: {str(e)}")

if __name__ == "__main__":
    main()
