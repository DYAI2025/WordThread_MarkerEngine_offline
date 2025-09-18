"""
WordThread Marker-Engine File Monitor
Real-time file system monitoring for OUTBOX directory with automatic data refresh
"""

import streamlit as st
import os
import time
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from datetime import datetime, timedelta
import pandas as pd

# Import existing processing functions
from components.data_validation import validate_analysis_bundle, validate_sqlite_data, validate_promatra_handshake
from utils.data_processing import process_analysis_bundle, process_sqlite_data
from utils.sqlite_handler import SQLiteHandler

class WordThreadFileHandler(FileSystemEventHandler):
    """Custom file handler for WordThread Marker-Engine files"""
    
    def __init__(self, callback_func=None):
        """Initialize with callback function for file processing"""
        super().__init__()
        self.callback_func = callback_func
        self.supported_extensions = ['.json', '.sqlite', '.db']
        self.processing_files = set()  # Track files currently being processed
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self.handle_file_event(event.src_path, 'created')
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self.handle_file_event(event.src_path, 'modified')
    
    def on_moved(self, event):
        """Handle file move events"""
        if not event.is_directory:
            self.handle_file_event(event.dest_path, 'moved')
    
    def handle_file_event(self, file_path: str, event_type: str):
        """Handle file system events for supported file types"""
        try:
            file_path = Path(file_path)
            
            # Check if file has supported extension
            if file_path.suffix.lower() not in self.supported_extensions:
                return
            
            # Avoid processing the same file multiple times
            if str(file_path) in self.processing_files:
                return
            
            # Wait for file to be completely written (simple approach)
            self.wait_for_file_stability(file_path)
            
            # Add to processing set
            self.processing_files.add(str(file_path))
            
            # Log the event
            self.log_file_event(file_path, event_type)
            
            # Process the file if callback is available
            if self.callback_func:
                self.callback_func(file_path, event_type)
            
        except Exception as e:
            self.log_error(f"Error handling file event for {file_path}: {str(e)}")
        finally:
            # Remove from processing set
            self.processing_files.discard(str(file_path))
    
    def wait_for_file_stability(self, file_path: Path, timeout: int = 10):
        """Wait for file to be completely written by checking size stability"""
        if not file_path.exists():
            return
        
        start_time = time.time()
        last_size = -1
        
        while time.time() - start_time < timeout:
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    # File size stable, assume write complete
                    time.sleep(0.5)  # Small additional delay
                    return
                last_size = current_size
                time.sleep(0.5)
            except (OSError, IOError):
                # File might be locked or still being written
                time.sleep(0.5)
                continue
    
    def log_file_event(self, file_path: Path, event_type: str):
        """Log file events to session state"""
        if 'file_monitor_log' not in st.session_state:
            st.session_state.file_monitor_log = []
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file_path': str(file_path),
            'file_name': file_path.name,
            'event_type': event_type,
            'file_size': file_path.stat().st_size if file_path.exists() else 0
        }
        
        st.session_state.file_monitor_log.append(log_entry)
        
        # Keep only last 100 entries
        if len(st.session_state.file_monitor_log) > 100:
            st.session_state.file_monitor_log = st.session_state.file_monitor_log[-100:]
    
    def log_error(self, error_message: str):
        """Log errors to session state"""
        if 'file_monitor_errors' not in st.session_state:
            st.session_state.file_monitor_errors = []
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error_message
        }
        
        st.session_state.file_monitor_errors.append(error_entry)
        
        # Keep only last 50 errors
        if len(st.session_state.file_monitor_errors) > 50:
            st.session_state.file_monitor_errors = st.session_state.file_monitor_errors[-50:]


class FileMonitorManager:
    """Manages file system monitoring for WordThread Marker-Engine"""
    
    def __init__(self, outbox_path: str = "./OUTBOX"):
        """Initialize file monitor manager"""
        self.outbox_path = Path(outbox_path)
        self.observer = None
        self.file_handler = None
        self.is_monitoring = False
        
        # Ensure OUTBOX directory exists
        self.outbox_path.mkdir(exist_ok=True)
    
    def start_monitoring(self):
        """Start file system monitoring"""
        if self.is_monitoring:
            return False
        
        try:
            # Create file handler with processing callback
            self.file_handler = WordThreadFileHandler(callback_func=self.process_detected_file)
            
            # Create and configure observer
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                str(self.outbox_path),
                recursive=True
            )
            
            # Start monitoring
            self.observer.start()
            self.is_monitoring = True
            
            # Log monitoring start
            self.log_monitoring_event("File monitoring started", "info")
            
            return True
            
        except Exception as e:
            self.log_monitoring_event(f"Failed to start monitoring: {str(e)}", "error")
            return False
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if not self.is_monitoring or not self.observer:
            return False
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.is_monitoring = False
            
            # Log monitoring stop
            self.log_monitoring_event("File monitoring stopped", "info")
            
            return True
            
        except Exception as e:
            self.log_monitoring_event(f"Error stopping monitoring: {str(e)}", "error")
            return False
    
    def process_detected_file(self, file_path: Path, event_type: str):
        """Process automatically detected files"""
        try:
            # Validate file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return
            
            # Create pseudo uploaded file object
            file_info = {
                'name': file_path.name,
                'path': str(file_path),
                'size': file_path.stat().st_size,
                'detected_at': datetime.now().isoformat(),
                'event_type': event_type
            }
            
            # Process based on file type
            success = False
            if file_path.suffix.lower() == '.json':
                success = self.process_json_file(file_path, file_info)
            elif file_path.suffix.lower() in ['.sqlite', '.db']:
                success = self.process_sqlite_file(file_path, file_info)
            
            # Update processing statistics
            self.update_processing_stats(file_info, success)
            
            # Trigger UI refresh
            if success:
                self.trigger_ui_refresh()
            
        except Exception as e:
            self.log_monitoring_event(f"Error processing file {file_path}: {str(e)}", "error")
    
    def process_json_file(self, file_path: Path, file_info: Dict) -> bool:
        """Process JSON files (AnalysisBundle or PromatraHandshake)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Determine file type and validate
            if 'bundle_version' in content or 'bundle' in content:
                # AnalysisBundle detected
                validation_result = validate_analysis_bundle(content)
                
                if validation_result['valid']:
                    processed_data = process_analysis_bundle(content)
                    st.session_state.analysis_data = processed_data
                    st.session_state.data_loaded = True
                    
                    self.log_monitoring_event(
                        f"Successfully processed AnalysisBundle: {file_path.name}", 
                        "success"
                    )
                    return True
                else:
                    self.log_monitoring_event(
                        f"AnalysisBundle validation failed for {file_path.name}: {validation_result['errors']}", 
                        "error"
                    )
                    
            elif 'version' in content and content.get('version') == '0.2' and 'handshake_id' in content:
                # PromatraHandshake v0.2 detected
                validation_result = validate_promatra_handshake(content)
                
                if validation_result['valid']:
                    st.session_state.promatra_handshake = validation_result
                    st.session_state.data_loaded = True
                    
                    self.log_monitoring_event(
                        f"Successfully processed PromatraHandshake v0.2: {file_path.name}", 
                        "success"
                    )
                    return True
                else:
                    self.log_monitoring_event(
                        f"PromatraHandshake validation failed for {file_path.name}: {validation_result['errors']}", 
                        "error"
                    )
            else:
                self.log_monitoring_event(
                    f"Unknown JSON file format: {file_path.name}", 
                    "warning"
                )
            
            return False
            
        except Exception as e:
            self.log_monitoring_event(
                f"Error processing JSON file {file_path.name}: {str(e)}", 
                "error"
            )
            return False
    
    def process_sqlite_file(self, file_path: Path, file_info: Dict) -> bool:
        """Process SQLite database files"""
        try:
            # Use existing SQLite handler
            with SQLiteHandler(str(file_path)) as handler:
                extracted_data = handler.extract_data()
                
                if 'error' in extracted_data:
                    self.log_monitoring_event(
                        f"SQLite extraction failed for {file_path.name}: {extracted_data['error']}", 
                        "error"
                    )
                    return False
                
                # Validate extracted data
                validation_result = validate_sqlite_data(extracted_data)
                
                if validation_result['valid']:
                    processed_data = process_sqlite_data(extracted_data)
                    st.session_state.sqlite_data = processed_data
                    st.session_state.data_loaded = True
                    
                    self.log_monitoring_event(
                        f"Successfully processed SQLite database: {file_path.name}", 
                        "success"
                    )
                    return True
                else:
                    self.log_monitoring_event(
                        f"SQLite validation failed for {file_path.name}: {validation_result['errors']}", 
                        "error"
                    )
                    return False
                    
        except Exception as e:
            self.log_monitoring_event(
                f"Error processing SQLite file {file_path.name}: {str(e)}", 
                "error"
            )
            return False
    
    def trigger_ui_refresh(self):
        """Trigger UI refresh after successful file processing"""
        # Update view state
        st.session_state.last_refresh = datetime.now().isoformat()
        
        # Force rerun to refresh UI
        st.rerun()
    
    def log_monitoring_event(self, message: str, level: str = "info"):
        """Log monitoring events"""
        if 'monitoring_log' not in st.session_state:
            st.session_state.monitoring_log = []
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        
        st.session_state.monitoring_log.append(log_entry)
        
        # Keep only last 100 entries
        if len(st.session_state.monitoring_log) > 100:
            st.session_state.monitoring_log = st.session_state.monitoring_log[-100:]
    
    def update_processing_stats(self, file_info: Dict, success: bool):
        """Update file processing statistics"""
        if 'monitoring_stats' not in st.session_state:
            st.session_state.monitoring_stats = {
                'total_files_detected': 0,
                'files_processed_successfully': 0,
                'files_failed': 0,
                'last_processed_file': None,
                'monitoring_started': datetime.now().isoformat()
            }
        
        stats = st.session_state.monitoring_stats
        stats['total_files_detected'] += 1
        
        if success:
            stats['files_processed_successfully'] += 1
            stats['last_processed_file'] = file_info['name']
        else:
            stats['files_failed'] += 1
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'outbox_path': str(self.outbox_path),
            'outbox_exists': self.outbox_path.exists(),
            'file_count': len(list(self.outbox_path.rglob('*'))) if self.outbox_path.exists() else 0
        }


def render_file_monitor_panel():
    """Render the file monitoring panel interface"""
    
    # WordThread branding header
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #FF4500, #FFD700);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(255, 69, 0, 0.3);
    ">
        <h2 style="color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            📁 Real-Time File Monitor
        </h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Automatic detection and processing of OUTBOX directory changes
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize file monitor manager if not exists
    if 'file_monitor_manager' not in st.session_state:
        st.session_state.file_monitor_manager = FileMonitorManager()
    
    monitor = st.session_state.file_monitor_manager
    
    # Tabbed interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Monitor Control", 
        "📊 Processing Stats", 
        "📋 Activity Log", 
        "⚙️ Configuration"
    ])
    
    with tab1:
        render_monitor_control(monitor)
    
    with tab2:
        render_processing_stats()
    
    with tab3:
        render_activity_log()
    
    with tab4:
        render_monitor_configuration(monitor)


def render_monitor_control(monitor: FileMonitorManager):
    """Render monitoring control interface"""
    
    st.markdown("#### 🎯 Monitor Control")
    
    # Get current status
    status = monitor.get_monitoring_status()
    
    # Status display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if status['is_monitoring'] else "🔴"
        st.metric(
            "Monitor Status", 
            f"{status_color} {'Active' if status['is_monitoring'] else 'Inactive'}"
        )
    
    with col2:
        st.metric("OUTBOX Path", f"📁 {status['outbox_path']}")
    
    with col3:
        exists_icon = "✅" if status['outbox_exists'] else "❌"
        st.metric("Directory", f"{exists_icon} {'Exists' if status['outbox_exists'] else 'Missing'}")
    
    with col4:
        st.metric("Files in OUTBOX", f"📄 {status['file_count']}")
    
    # Control buttons
    st.markdown("**Monitor Control:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🟢 Start Monitoring", disabled=status['is_monitoring']):
            if monitor.start_monitoring():
                st.success("✅ File monitoring started!")
                st.rerun()
            else:
                st.error("❌ Failed to start monitoring. Check logs for details.")
    
    with col2:
        if st.button("🔴 Stop Monitoring", disabled=not status['is_monitoring']):
            if monitor.stop_monitoring():
                st.success("✅ File monitoring stopped!")
                st.rerun()
            else:
                st.error("❌ Failed to stop monitoring.")
    
    with col3:
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    # Manual file scan
    st.markdown("**Manual Operations:**")
    
    if st.button("🔍 Scan OUTBOX Directory"):
        scan_results = scan_outbox_directory(monitor.outbox_path)
        
        if scan_results['files']:
            st.markdown("**Files found in OUTBOX:**")
            for file_info in scan_results['files']:
                st.write(f"• {file_info['name']} ({format_file_size(file_info['size'])})")
        else:
            st.info("No supported files found in OUTBOX directory.")


def render_processing_stats():
    """Render file processing statistics"""
    
    st.markdown("#### 📊 Processing Statistics")
    
    if 'monitoring_stats' not in st.session_state:
        st.info("No processing statistics available. Start monitoring to see stats.")
        return
    
    stats = st.session_state.monitoring_stats
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Files Detected", stats['total_files_detected'])
    
    with col2:
        st.metric("Successfully Processed", stats['files_processed_successfully'])
    
    with col3:
        st.metric("Failed Processing", stats['files_failed'])
    
    with col4:
        success_rate = 0
        if stats['total_files_detected'] > 0:
            success_rate = stats['files_processed_successfully'] / stats['total_files_detected']
        st.metric("Success Rate", f"{success_rate:.1%}")
    
    # Recent activity
    if stats.get('last_processed_file'):
        st.markdown(f"**Last Processed File:** {stats['last_processed_file']}")
    
    st.markdown(f"**Monitoring Started:** {stats['monitoring_started']}")
    
    # Processing timeline (if available)
    if 'file_monitor_log' in st.session_state and st.session_state.file_monitor_log:
        st.markdown("**Recent File Events:**")
        
        recent_events = st.session_state.file_monitor_log[-10:]  # Last 10 events
        events_df = pd.DataFrame(recent_events)
        
        if not events_df.empty:
            # Format for display
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp']).dt.strftime('%H:%M:%S')
            events_df['size_mb'] = events_df['file_size'].apply(lambda x: f"{x/(1024*1024):.2f} MB")
            
            display_df = events_df[['timestamp', 'file_name', 'event_type', 'size_mb']]
            display_df.columns = ['Time', 'File', 'Event', 'Size']
            
            st.dataframe(display_df, use_container_width=True)


def render_activity_log():
    """Render activity log interface"""
    
    st.markdown("#### 📋 Activity Log")
    
    # Log level filter
    log_levels = ["All", "info", "success", "warning", "error"]
    selected_level = st.selectbox("Filter by Level", log_levels, key="log_level_filter")
    
    # Display monitoring log
    if 'monitoring_log' in st.session_state and st.session_state.monitoring_log:
        
        logs = st.session_state.monitoring_log
        
        # Filter by level
        if selected_level != "All":
            logs = [log for log in logs if log['level'] == selected_level]
        
        if logs:
            st.markdown(f"**Showing {len(logs)} log entries:**")
            
            for log_entry in reversed(logs[-20:]):  # Show last 20 entries, most recent first
                
                # Color code by level
                level_colors = {
                    'info': '#2196F3',
                    'success': '#4CAF50',
                    'warning': '#FF9800',
                    'error': '#F44336'
                }
                
                level_color = level_colors.get(log_entry['level'], '#607D8B')
                
                st.markdown(f"""
                <div style="
                    border-left: 4px solid {level_color};
                    padding: 0.5rem;
                    margin: 0.3rem 0;
                    background: rgba(255,255,255,0.05);
                    border-radius: 0 5px 5px 0;
                ">
                    <strong style="color: {level_color};">{log_entry['level'].upper()}</strong>
                    - {log_entry['message']}
                    <br><small>🕒 {log_entry['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No {selected_level} level logs to display.")
    else:
        st.info("No activity logs available. Start monitoring to see activity.")
    
    # Clear logs button
    if st.button("🗑️ Clear Activity Log"):
        if 'monitoring_log' in st.session_state:
            st.session_state.monitoring_log = []
        if 'file_monitor_log' in st.session_state:
            st.session_state.file_monitor_log = []
        if 'file_monitor_errors' in st.session_state:
            st.session_state.file_monitor_errors = []
        st.success("Activity log cleared!")
        st.rerun()


def render_monitor_configuration(monitor: FileMonitorManager):
    """Render monitor configuration interface"""
    
    st.markdown("#### ⚙️ Monitor Configuration")
    
    # OUTBOX path configuration
    st.markdown("**OUTBOX Directory Settings:**")
    
    current_path = str(monitor.outbox_path)
    new_path = st.text_input(
        "OUTBOX Directory Path",
        value=current_path,
        help="Path to the directory to monitor for new files"
    )
    
    if new_path != current_path:
        if st.button("📁 Update OUTBOX Path"):
            # Stop monitoring if active
            if monitor.is_monitoring:
                monitor.stop_monitoring()
            
            # Update path
            monitor.outbox_path = Path(new_path)
            monitor.outbox_path.mkdir(exist_ok=True)
            
            st.success(f"OUTBOX path updated to: {new_path}")
            st.rerun()
    
    # File type settings
    st.markdown("**Supported File Types:**")
    st.write("• **JSON**: AnalysisBundle and PromatraHandshake v0.2 files")
    st.write("• **SQLite**: Database files (.db, .sqlite)")
    
    # Monitoring settings
    st.markdown("**Monitoring Settings:**")
    
    recursive_monitoring = st.checkbox(
        "Monitor subdirectories",
        value=True,
        help="Monitor all subdirectories within OUTBOX"
    )
    
    file_stability_timeout = st.slider(
        "File stability timeout (seconds)",
        min_value=1,
        max_value=30,
        value=10,
        help="Wait time to ensure file is completely written before processing"
    )
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        
        max_log_entries = st.number_input(
            "Maximum log entries to keep",
            min_value=50,
            max_value=1000,
            value=100,
            help="Number of log entries to retain in memory"
        )
        
        auto_refresh_ui = st.checkbox(
            "Auto-refresh UI after processing",
            value=True,
            help="Automatically refresh the interface when new files are processed"
        )
        
        show_debug_info = st.checkbox(
            "Show debug information",
            value=False,
            help="Display additional debug information in logs"
        )
    
    # Directory utilities
    st.markdown("**Directory Utilities:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Create OUTBOX Directory"):
            monitor.outbox_path.mkdir(exist_ok=True)
            st.success(f"OUTBOX directory created at: {monitor.outbox_path}")
    
    with col2:
        if st.button("📂 Open OUTBOX in Explorer"):
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(f'explorer "{monitor.outbox_path}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(f'open "{monitor.outbox_path}"', shell=True)
            else:  # Linux
                subprocess.run(f'xdg-open "{monitor.outbox_path}"', shell=True)


def scan_outbox_directory(outbox_path: Path) -> Dict[str, Any]:
    """Scan OUTBOX directory for supported files"""
    
    results = {
        'files': [],
        'total_size': 0,
        'supported_extensions': ['.json', '.sqlite', '.db']
    }
    
    if not outbox_path.exists():
        return results
    
    try:
        for file_path in outbox_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in results['supported_extensions']:
                file_info = {
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'extension': file_path.suffix.lower(),
                    'modified': file_path.stat().st_mtime
                }
                
                results['files'].append(file_info)
                results['total_size'] += file_info['size']
        
        # Sort by modification time (newest first)
        results['files'].sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        results['error'] = str(e)
    
    return results


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