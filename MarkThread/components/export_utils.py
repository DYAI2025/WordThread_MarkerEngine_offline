import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, List
import datetime

def export_png(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> Optional[bytes]:
    """Export current charts and visualizations as PNG"""
    
    try:
        # Create a comprehensive visualization for export
        export_fig = create_export_visualization(analysis_data, sqlite_data)
        
        if export_fig is None:
            st.error("No data available for PNG export")
            return None
        
        # Convert plotly figure to PNG
        img_bytes = export_fig.to_image(format="png", width=1920, height=1080, scale=2)
        
        return img_bytes
    
    except Exception as e:
        st.error(f"Error creating PNG export: {str(e)}")
        return None

def export_json(view_state: Dict[str, Any]) -> str:
    """Export current view state as JSON"""
    
    try:
        # Create comprehensive export data
        export_data = {
            'export_metadata': {
                'timestamp': datetime.datetime.now().isoformat(),
                'export_type': 'wordthread_marker_analysis',
                'version': '1.0'
            },
            'view_state': view_state,
            'analysis_summary': generate_analysis_summary(view_state),
            'export_info': {
                'application': 'WordThread Marker-Engine Frontend',
                'export_format': 'JSON',
                'data_sources': determine_data_sources(view_state)
            }
        }
        
        # Convert to JSON string with proper formatting
        json_string = json.dumps(export_data, indent=2, default=str)
        
        return json_string
    
    except Exception as e:
        st.error(f"Error creating JSON export: {str(e)}")
        return json.dumps({'error': str(e)}, indent=2)

def create_export_visualization(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> Optional[go.Figure]:
    """Create a comprehensive visualization for export"""
    
    if not analysis_data and not sqlite_data:
        return None
    
    # Prepare data for visualization
    combined_data = prepare_export_data(analysis_data, sqlite_data)
    
    if combined_data.empty:
        return None
    
    # Create subplot figure with multiple charts
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Marker Activity Over Time',
            'Marker Category Distribution',
            'Hourly Activity Pattern',
            'Top Active Markers'
        ],
        specs=[
            [{"secondary_y": False}, {"type": "pie"}],
            [{"type": "heatmap"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Chart 1: Time series of marker activity
    if 'timestamp' in combined_data.columns and 'marker_id' in combined_data.columns:
        # Aggregate by hour
        hourly_data = combined_data.set_index('timestamp').resample('1H').size().reset_index()
        hourly_data.columns = ['timestamp', 'count']
        
        fig.add_trace(
            go.Scatter(
                x=hourly_data['timestamp'],
                y=hourly_data['count'],
                mode='lines+markers',
                name='Activity',
                line=dict(color='#FF8C00', width=2),
                fill='tozeroy',
                fillcolor='rgba(255,140,0,0.3)'
            ),
            row=1, col=1
        )
    
    # Chart 2: Marker category distribution
    if 'marker_category' in combined_data.columns:
        category_counts = combined_data['marker_category'].value_counts()
        
        fig.add_trace(
            go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                name="Categories",
                marker=dict(colors=['#FF8C00', '#FFD700', '#FFA500', '#FF6347'])
            ),
            row=1, col=2
        )
    
    # Chart 3: Hourly activity heatmap
    if 'timestamp' in combined_data.columns:
        combined_data['hour'] = combined_data['timestamp'].dt.hour
        combined_data['date'] = combined_data['timestamp'].dt.date
        
        heatmap_data = combined_data.pivot_table(
            values='id',
            index='date',
            columns='hour',
            aggfunc='count',
            fill_value=0
        )
        
        # Limit to last 30 days or first 30 days if more data
        if len(heatmap_data) > 30:
            heatmap_data = heatmap_data.tail(30)
        
        fig.add_trace(
            go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=[str(date) for date in heatmap_data.index],
                colorscale='OrRd',
                name="Activity"
            ),
            row=2, col=1
        )
    
    # Chart 4: Top active markers
    if 'marker_id' in combined_data.columns:
        top_markers = combined_data['marker_id'].value_counts().head(10)
        
        fig.add_trace(
            go.Bar(
                y=top_markers.index,
                x=top_markers.values,
                orientation='h',
                name='Markers',
                marker=dict(color='rgba(255,140,0,0.7)')
            ),
            row=2, col=2
        )
    
    # Update layout with WordThread styling
    fig.update_layout(
        title={
            'text': 'WordThread Marker-Engine Analysis Export',
            'x': 0.5,
            'font': {'size': 24, 'color': '#FFD700'}
        },
        plot_bgcolor='rgba(14,14,14,1)',
        paper_bgcolor='rgba(14,14,14,1)',
        font_color='white',
        font_family="Arial, sans-serif",
        height=1080,
        width=1920,
        showlegend=False
    )
    
    # Add export timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fig.add_annotation(
        text=f"Generated: {current_time}",
        xref="paper", yref="paper",
        x=0.99, y=0.01,
        showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.6)"),
        align="right"
    )
    
    return fig

def prepare_export_data(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare combined data for export visualization"""
    
    data_frames = []
    
    # Process analysis bundle data
    if analysis_data and 'hits' in analysis_data:
        hits_df = pd.DataFrame(analysis_data['hits'])
        
        if not hits_df.empty:
            # Convert timestamp
            if 'ts' in hits_df.columns:
                hits_df['timestamp'] = pd.to_datetime(hits_df['ts'], unit='s')
            
            # Add marker categories
            hits_df['marker_category'] = hits_df['marker_id'].apply(categorize_marker_for_export)
            hits_df['source'] = 'analysis_bundle'
            data_frames.append(hits_df)
    
    # Process SQLite data
    if sqlite_data and 'tables' in sqlite_data and 'hits' in sqlite_data['tables']:
        sqlite_hits = pd.DataFrame(sqlite_data['tables']['hits'])
        
        if not sqlite_hits.empty:
            # Standardize columns
            if 'ts' in sqlite_hits.columns:
                sqlite_hits['timestamp'] = pd.to_datetime(sqlite_hits['ts'], unit='s')
            
            sqlite_hits['marker_category'] = sqlite_hits['marker_id'].apply(categorize_marker_for_export)
            sqlite_hits['source'] = 'sqlite'
            data_frames.append(sqlite_hits)
    
    # Combine data
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        return combined_df
    
    return pd.DataFrame()

def categorize_marker_for_export(marker_id: str) -> str:
    """Categorize marker for export visualization"""
    if marker_id.startswith('ATO_'):
        return 'ATO'
    elif marker_id.startswith('SEM_'):
        return 'SEM'
    elif marker_id.startswith('CLU_'):
        return 'CLU'
    elif marker_id.startswith('MEMA_'):
        return 'MEMA'
    else:
        return 'OTHER'

def generate_analysis_summary(view_state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate analysis summary for JSON export"""
    
    summary = {
        'data_availability': {
            'has_analysis_data': view_state.get('has_analysis_data', False),
            'has_sqlite_data': view_state.get('has_sqlite_data', False),
            'data_loaded': view_state.get('data_loaded', False)
        },
        'filters_applied': {
            'selected_markers': view_state.get('selected_markers', []),
            'time_filter': view_state.get('time_filter')
        },
        'analysis_scope': determine_analysis_scope(view_state),
        'recommendations': generate_export_recommendations(view_state)
    }
    
    return summary

def determine_analysis_scope(view_state: Dict[str, Any]) -> Dict[str, Any]:
    """Determine the scope of analysis based on view state"""
    
    scope = {
        'temporal_analysis': False,
        'marker_analysis': False,
        'drift_analysis': False,
        'evidence_analysis': False
    }
    
    # Determine scope based on available data
    if view_state.get('has_analysis_data') or view_state.get('has_sqlite_data'):
        scope['marker_analysis'] = True
        scope['evidence_analysis'] = True
        
        if view_state.get('time_filter'):
            scope['temporal_analysis'] = True
            scope['drift_analysis'] = True
    
    return scope

def determine_data_sources(view_state: Dict[str, Any]) -> List[str]:
    """Determine data sources used in the analysis"""
    
    sources = []
    
    if view_state.get('has_analysis_data'):
        sources.append('AnalysisBundle_JSON')
    
    if view_state.get('has_sqlite_data'):
        sources.append('SQLite_Database')
    
    if not sources:
        sources.append('No_Data_Loaded')
    
    return sources

def generate_export_recommendations(view_state: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on current analysis state"""
    
    recommendations = []
    
    # Data availability recommendations
    if not view_state.get('data_loaded', False):
        recommendations.append("Upload data files to begin analysis")
        return recommendations
    
    # Filter recommendations
    selected_markers = view_state.get('selected_markers', [])
    if not selected_markers:
        recommendations.append("Consider selecting specific markers for focused analysis")
    elif len(selected_markers) > 20:
        recommendations.append("Large number of markers selected - consider filtering for better visualization")
    
    # Time filter recommendations
    if not view_state.get('time_filter'):
        recommendations.append("Apply time filters to analyze temporal patterns and drift")
    
    # Data source recommendations
    has_analysis = view_state.get('has_analysis_data', False)
    has_sqlite = view_state.get('has_sqlite_data', False)
    
    if has_analysis and not has_sqlite:
        recommendations.append("Consider uploading SQLite data for enhanced analysis capabilities")
    elif has_sqlite and not has_analysis:
        recommendations.append("Consider uploading AnalysisBundle JSON for comprehensive marker analysis")
    
    # Analysis recommendations
    if has_analysis or has_sqlite:
        recommendations.append("Explore drift analysis to identify temporal changes in marker patterns")
        recommendations.append("Review evidence panel for detailed marker insights and provenance")
        recommendations.append("Export results in multiple formats for further analysis")
    
    if not recommendations:
        recommendations.append("Analysis configuration appears complete - continue exploring insights")
    
    return recommendations

def create_summary_image(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> Optional[Image.Image]:
    """Create a summary image with key statistics"""
    
    try:
        # Create a basic summary image
        img = Image.new('RGB', (800, 600), color='#0E0E0E')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_medium = ImageFont.truetype("arial.ttf", 18)
            font_small = ImageFont.truetype("arial.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Header
        draw.text((50, 50), "WordThread Marker-Engine", font=font_large, fill='#FFD700')
        draw.text((50, 80), "Analysis Summary", font=font_medium, fill='#FF8C00')
        
        y_position = 130
        
        # Calculate basic statistics
        total_hits = 0
        unique_markers = 0
        data_sources = []
        
        if analysis_data and 'hits' in analysis_data:
            hits_df = pd.DataFrame(analysis_data['hits'])
            total_hits += len(hits_df)
            unique_markers += hits_df['marker_id'].nunique() if 'marker_id' in hits_df.columns else 0
            data_sources.append("AnalysisBundle")
        
        if sqlite_data and 'tables' in sqlite_data and 'hits' in sqlite_data['tables']:
            sqlite_hits = pd.DataFrame(sqlite_data['tables']['hits'])
            total_hits += len(sqlite_hits)
            unique_markers += sqlite_hits['marker_id'].nunique() if 'marker_id' in sqlite_hits.columns else 0
            data_sources.append("SQLite")
        
        # Display statistics
        draw.text((50, y_position), f"Total Hits: {total_hits:,}", font=font_medium, fill='white')
        y_position += 40
        
        draw.text((50, y_position), f"Unique Markers: {unique_markers}", font=font_medium, fill='white')
        y_position += 40
        
        draw.text((50, y_position), f"Data Sources: {', '.join(data_sources) if data_sources else 'None'}", font=font_medium, fill='white')
        y_position += 40
        
        # Timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((50, 550), f"Generated: {timestamp}", font=font_small, fill='rgba(255,255,255,0.6)')
        
        return img
    
    except Exception as e:
        st.error(f"Error creating summary image: {str(e)}")
        return None

def validate_export_data(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate data before export"""
    
    validation = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'data_summary': {}
    }
    
    try:
        # Check data availability
        if not analysis_data and not sqlite_data:
            validation['errors'].append("No data available for export")
            return validation
        
        # Validate analysis data
        if analysis_data:
            if 'hits' not in analysis_data:
                validation['warnings'].append("AnalysisBundle missing hits data")
            else:
                hits_count = len(analysis_data['hits'])
                validation['data_summary']['analysis_hits'] = hits_count
                
                if hits_count == 0:
                    validation['warnings'].append("AnalysisBundle contains no hits")
        
        # Validate SQLite data
        if sqlite_data:
            if 'tables' not in sqlite_data:
                validation['warnings'].append("SQLite data missing table information")
            elif 'hits' not in sqlite_data['tables']:
                validation['warnings'].append("SQLite data missing hits table")
            else:
                sqlite_hits = len(sqlite_data['tables']['hits'])
                validation['data_summary']['sqlite_hits'] = sqlite_hits
                
                if sqlite_hits == 0:
                    validation['warnings'].append("SQLite hits table is empty")
        
        # Determine if export is valid
        total_hits = validation['data_summary'].get('analysis_hits', 0) + validation['data_summary'].get('sqlite_hits', 0)
        
        if total_hits > 0:
            validation['valid'] = True
        else:
            validation['errors'].append("No valid hit data found for export")
    
    except Exception as e:
        validation['errors'].append(f"Validation error: {str(e)}")
    
    return validation
