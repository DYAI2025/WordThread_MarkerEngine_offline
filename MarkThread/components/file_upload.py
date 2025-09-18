import streamlit as st
import json
from typing import List, Optional

def render_file_upload() -> Optional[List]:
    """Render file upload interface with drag-and-drop support"""
    
    st.markdown("#### Upload Data Files")
    st.markdown("Supported formats: JSON (AnalysisBundle), SQLite (.db, .sqlite)")
    
    # File uploader with multiple file support
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['json', 'sqlite', 'db'],
        accept_multiple_files=True,
        help="Upload AnalysisBundle JSON files or SQLite databases containing marker data"
    )
    
    if uploaded_files:
        st.markdown("#### 📁 Uploaded Files")
        
        for file in uploaded_files:
            # Display file information
            file_size = len(file.getvalue())
            file_size_mb = file_size / (1024 * 1024)
            
            with st.expander(f"📄 {file.name} ({file_size_mb:.2f} MB)", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Type:** {file.type}")
                
                with col2:
                    st.write(f"**Size:** {file_size:,} bytes")
                
                with col3:
                    if file.name.endswith('.json'):
                        try:
                            # Preview JSON structure
                            content = json.loads(file.getvalue().decode('utf-8'))
                            st.write(f"**Keys:** {', '.join(list(content.keys())[:5])}")
                            if len(content.keys()) > 5:
                                st.write("...")
                        except:
                            st.write("**Status:** Invalid JSON")
                    else:
                        st.write(f"**Format:** SQLite Database")
        
        # Processing status
        if len(uploaded_files) > 0:
            st.info(f"📤 {len(uploaded_files)} file(s) ready for processing. Processing will begin automatically.")
    
    else:
        # Show drag-and-drop guidance
        st.markdown("""
        <div style="
            border: 2px dashed #FF8C00;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
            background: linear-gradient(135deg, rgba(255,140,0,0.1) 0%, rgba(255,215,0,0.1) 100%);
        ">
            <h4>📁 Drag & Drop Files Here</h4>
            <p>Or click "Browse files" above</p>
            <small>Supported: .json, .sqlite, .db</small>
        </div>
        """, unsafe_allow_html=True)
    
    return uploaded_files

def validate_file_format(file) -> dict:
    """Validate file format and return validation result"""
    result = {
        'valid': False,
        'type': None,
        'errors': []
    }
    
    try:
        if file.name.endswith('.json'):
            # Validate JSON format
            content = json.loads(file.getvalue().decode('utf-8'))
            result['valid'] = True
            result['type'] = 'json'
            
            # Basic structure validation
            if 'bundle' not in content:
                result['errors'].append("Missing required 'bundle' field")
            if 'hits' not in content:
                result['errors'].append("Missing required 'hits' field")
                
        elif file.name.endswith(('.sqlite', '.db')):
            # Basic SQLite validation (more detailed validation in sqlite_handler)
            result['valid'] = True
            result['type'] = 'sqlite'
            
        else:
            result['errors'].append(f"Unsupported file type: {file.name}")
    
    except json.JSONDecodeError as e:
        result['errors'].append(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        result['errors'].append(f"File validation error: {str(e)}")
    
    return result

def show_upload_progress(files: List, progress_callback=None):
    """Show upload and processing progress"""
    if not files:
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(files):
        progress = (i + 1) / len(files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {file.name}...")
        
        if progress_callback:
            progress_callback(file, progress)
    
    status_text.text("✅ All files processed successfully!")
    progress_bar.progress(1.0)
