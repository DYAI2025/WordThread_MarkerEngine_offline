import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.performance import lttb_downsample, adaptive_downsample, should_downsample, performance_monitor, performance_timer

def render_charts(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]):
    """Render interactive charts for marker data"""
    
    if not analysis_data and not sqlite_data:
        st.info("📊 No data available for charting. Please upload data files.")
        return
    
    st.markdown("### 📊 Interactive Visualizations")
    
    # Chart type selection
    chart_type = st.selectbox(
        "Select Chart Type",
        ["Time Series", "Heatmap", "Distribution", "Correlation Matrix"],
        help="Choose the type of visualization to display"
    )
    
    # Prepare data for charting
    chart_data = prepare_chart_data(analysis_data, sqlite_data)
    
    if not chart_data or chart_data.empty:
        st.warning("⚠️ No valid data available for charting")
        return
    
    # Render selected chart type
    if chart_type == "Time Series":
        render_time_series_chart(chart_data)
    elif chart_type == "Heatmap":
        render_heatmap_chart(chart_data)
    elif chart_type == "Distribution":
        render_distribution_chart(chart_data)
    elif chart_type == "Correlation Matrix":
        render_correlation_matrix(chart_data)
    
    # Chart controls and options
    render_chart_controls(chart_data)

@performance_timer
def prepare_chart_data(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare and combine data from different sources for charting"""
    
    data_frames = []
    
    # Process analysis bundle data
    if analysis_data and 'hits' in analysis_data:
        hits_df = pd.DataFrame(analysis_data['hits'])
        
        # Convert timestamp to datetime
        if 'ts' in hits_df.columns:
            hits_df['timestamp'] = pd.to_datetime(hits_df['ts'], unit='s')
        
        # Add source identifier
        hits_df['source'] = 'analysis_bundle'
        data_frames.append(hits_df)
    
    # Process SQLite data
    if sqlite_data and 'tables' in sqlite_data and 'hits' in sqlite_data['tables']:
        sqlite_hits = pd.DataFrame(sqlite_data['tables']['hits'])
        
        # Standardize column names and types
        if 'ts' in sqlite_hits.columns:
            sqlite_hits['timestamp'] = pd.to_datetime(sqlite_hits['ts'], unit='s')
        
        sqlite_hits['source'] = 'sqlite'
        data_frames.append(sqlite_hits)
    
    # Combine all data
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        
        # Apply time filter if set
        if st.session_state.time_filter:
            time_range = st.session_state.time_filter
            if len(time_range) == 2 and 'timestamp' in combined_df.columns:
                start_date = pd.Timestamp(time_range[0])
                end_date = pd.Timestamp(time_range[1]) + pd.Timedelta(days=1)  # Include full end date
                combined_df = combined_df[
                    (combined_df['timestamp'] >= start_date) & 
                    (combined_df['timestamp'] < end_date)
                ]
        
        # Apply downsampling for large datasets
        if should_downsample(combined_df, threshold=10000):
            st.info(f"📊 Large dataset detected ({len(combined_df):,} points). Applying intelligent downsampling for optimal performance.")
            
            if 'timestamp' in combined_df.columns:
                # Use LTTB downsampling to preserve visual characteristics
                original_size = len(combined_df)
                combined_df = lttb_downsample(combined_df, 'timestamp', 'ts', threshold=5000)
                downsample_ratio = len(combined_df) / original_size
                
                performance_monitor.record_processing(
                    'chart_data_downsampling', 
                    0,  # Duration will be recorded by decorator
                    original_size, 
                    downsample_ratio
                )
                
                st.success(f"✅ Downsampled to {len(combined_df):,} points (ratio: {downsample_ratio:.2f}) while preserving data patterns.")
        
        return combined_df
    
    return pd.DataFrame()

@performance_timer
def render_time_series_chart(data: pd.DataFrame):
    """Render time series line chart"""
    st.markdown("#### 📈 Time Series Analysis")
    
    if 'timestamp' not in data.columns:
        st.error("No timestamp data available for time series chart")
        return
    
    # Aggregate data by time intervals
    time_interval = st.selectbox(
        "Time Interval",
        ["5 min", "15 min", "1 hour", "1 day"],
        help="Select time interval for aggregation"
    )
    
    # Convert interval to pandas frequency
    interval_map = {
        "5 min": "5T",
        "15 min": "15T", 
        "1 hour": "1H",
        "1 day": "1D"
    }
    
    freq = interval_map[time_interval]
    
    # Group by marker_id and time interval
    if 'marker_id' in data.columns:
        # Aggregate by marker type
        time_series_data = data.set_index('timestamp').groupby('marker_id').resample(freq).size().reset_index()
        time_series_data.columns = ['marker_id', 'timestamp', 'count']
        
        # Create line chart with multiple series
        fig = px.line(
            time_series_data,
            x='timestamp',
            y='count',
            color='marker_id',
            title=f"Marker Hits Over Time ({time_interval} intervals)",
            labels={'count': 'Hit Count', 'timestamp': 'Time'}
        )
        
        # Customize layout with WordThread styling
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=16,
            legend=dict(
                bgcolor="rgba(0,0,0,0.8)",
                bordercolor="rgba(255,140,0,0.5)",
                borderwidth=1
            )
        )
        
        # Add gradient fill
        for trace in fig.data:
            trace.fill = 'tonexty' if trace.name != fig.data[0].name else 'tozeroy'
            trace.fillcolor = trace.line.color.replace('rgb', 'rgba').replace(')', ',0.3)')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics with performance info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Hits", len(data))
        with col2:
            st.metric("Unique Markers", data['marker_id'].nunique())
        with col3:
            if len(data) > 0:
                avg_hits_per_interval = time_series_data['count'].mean()
                st.metric("Avg Hits/Interval", f"{avg_hits_per_interval:.1f}")
        with col4:
            # Show performance metrics
            perf_summary = performance_monitor.get_performance_summary()
            if perf_summary.get('status') != 'no_data':
                st.metric(
                    "Performance Score", 
                    f"{perf_summary.get('performance_score', 0):.0f}/100",
                    help="Chart rendering performance score (higher is better)"
                )
    
    else:
        # Simple time series without marker grouping
        simple_ts = data.set_index('timestamp').resample(freq).size().reset_index()
        simple_ts.columns = ['timestamp', 'count']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=simple_ts['timestamp'],
            y=simple_ts['count'],
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(255,140,0,0.3)',
            line=dict(color='#FF8C00', width=2),
            name='Hit Count'
        ))
        
        fig.update_layout(
            title=f"Hit Count Over Time ({time_interval} intervals)",
            xaxis_title="Time",
            yaxis_title="Hit Count",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)

@performance_timer
def render_heatmap_chart(data: pd.DataFrame):
    """Render heatmap visualization"""
    st.markdown("#### 🔥 Pattern Heatmap")
    
    if 'marker_id' not in data.columns or 'timestamp' not in data.columns:
        st.error("Missing required columns for heatmap visualization")
        return
    
    # Create time-based heatmap
    heatmap_granularity = st.selectbox(
        "Heatmap Granularity",
        ["Hour of Day vs Marker", "Day of Week vs Marker", "Day vs Hour"],
        help="Select the dimensions for the heatmap"
    )
    
    if heatmap_granularity == "Hour of Day vs Marker":
        # Hour of day vs marker type
        data['hour'] = data['timestamp'].dt.hour
        heatmap_data = data.pivot_table(
            values='id', 
            index='marker_id', 
            columns='hour', 
            aggfunc='count', 
            fill_value=0
        )
        x_title = "Hour of Day"
        y_title = "Marker Type"
        
    elif heatmap_granularity == "Day of Week vs Marker":
        # Day of week vs marker type
        data['day_of_week'] = data['timestamp'].dt.day_name()
        heatmap_data = data.pivot_table(
            values='id', 
            index='marker_id', 
            columns='day_of_week', 
            aggfunc='count', 
            fill_value=0
        )
        x_title = "Day of Week"
        y_title = "Marker Type"
        
    else:  # Day vs Hour
        data['date'] = data['timestamp'].dt.date
        data['hour'] = data['timestamp'].dt.hour
        heatmap_data = data.pivot_table(
            values='id', 
            index='date', 
            columns='hour', 
            aggfunc='count', 
            fill_value=0
        )
        x_title = "Hour of Day"
        y_title = "Date"
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale=[
            [0, 'rgba(0,0,0,0.8)'],
            [0.3, 'rgba(255,140,0,0.3)'],
            [0.7, 'rgba(255,140,0,0.7)'],
            [1, 'rgba(255,215,0,1)']
        ],
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=f"Activity Heatmap: {heatmap_granularity}",
        xaxis_title=x_title,
        yaxis_title=y_title,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_distribution_chart(data: pd.DataFrame):
    """Render distribution charts"""
    st.markdown("#### 📊 Data Distribution")
    
    if 'marker_id' not in data.columns:
        st.error("No marker data available for distribution analysis")
        return
    
    # Distribution type selection
    dist_type = st.selectbox(
        "Distribution Type",
        ["Marker Frequency", "Time Distribution", "Conversation Distribution"],
        help="Select the type of distribution to analyze"
    )
    
    if dist_type == "Marker Frequency":
        # Marker frequency bar chart
        marker_counts = data['marker_id'].value_counts().head(20)  # Top 20 markers
        
        fig = go.Figure(data=[
            go.Bar(
                x=marker_counts.index,
                y=marker_counts.values,
                marker=dict(
                    color='rgba(255,140,0,0.7)',
                    line=dict(color='rgba(255,140,0,1)', width=1)
                )
            )
        ])
        
        fig.update_layout(
            title="Top Marker Frequencies",
            xaxis_title="Marker ID",
            yaxis_title="Frequency",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif dist_type == "Time Distribution" and 'timestamp' in data.columns:
        # Time-based distribution
        data['hour'] = data['timestamp'].dt.hour
        hour_dist = data['hour'].value_counts().sort_index()
        
        fig = go.Figure(data=[
            go.Scatter(
                x=hour_dist.index,
                y=hour_dist.values,
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(255,140,0,0.3)',
                line=dict(color='#FF8C00', width=2),
                marker=dict(size=8, color='#FFD700')
            )
        ])
        
        fig.update_layout(
            title="Activity by Hour of Day",
            xaxis_title="Hour",
            yaxis_title="Activity Count",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif dist_type == "Conversation Distribution" and 'conv' in data.columns:
        # Conversation distribution
        conv_counts = data['conv'].value_counts().head(15)
        
        fig = go.Figure(data=[
            go.Pie(
                labels=conv_counts.index,
                values=conv_counts.values,
                hole=0.4,
                marker=dict(
                    colors=['rgba(255,140,0,0.7)', 'rgba(255,215,0,0.7)', 'rgba(255,165,0,0.7)'] * 5
                )
            )
        ])
        
        fig.update_layout(
            title="Conversation Distribution",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_correlation_matrix(data: pd.DataFrame):
    """Render correlation matrix for numerical data"""
    st.markdown("#### 🔗 Correlation Analysis")
    
    # Find numerical columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        st.info("Insufficient numerical data for correlation analysis")
        return
    
    # Calculate correlation matrix
    corr_matrix = data[numeric_cols].corr()
    
    # Create correlation heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmid=0,
        text=np.around(corr_matrix.values, decimals=2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Feature Correlation Matrix",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_chart_controls(data: pd.DataFrame):
    """Render additional chart controls and options"""
    st.markdown("### ⚙️ Chart Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Data filtering options
        st.markdown("#### 🔍 Filters")
        
        if 'marker_id' in data.columns:
            unique_markers = data['marker_id'].unique().tolist()
            selected_markers = st.multiselect(
                "Select Markers",
                unique_markers,
                default=unique_markers[:10] if len(unique_markers) > 10 else unique_markers,
                help="Choose specific markers to display"
            )
            st.session_state.selected_markers = selected_markers
    
    with col2:
        # Display options
        st.markdown("#### 🎨 Display")
        
        show_grid = st.checkbox("Show Grid", value=True)
        show_legend = st.checkbox("Show Legend", value=True)
        
        # Animation options
        enable_animations = st.checkbox("Enable Animations", value=True)
    
    with col3:
        # Performance options
        st.markdown("#### ⚡ Performance")
        
        max_points = st.slider(
            "Max Data Points",
            min_value=100,
            max_value=10000,
            value=5000,
            help="Limit data points for better performance"
        )
        
        if len(data) > max_points:
            st.info(f"Data will be sampled to {max_points} points for performance")

def apply_wordthread_styling(fig):
    """Apply WordThread branding to plotly figures"""
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        font_family="Arial, sans-serif",
        title_font_size=18,
        title_font_color='#FFD700',
        legend=dict(
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor="rgba(255,140,0,0.5)",
            borderwidth=1,
            font_color='white'
        ),
        xaxis=dict(
            gridcolor='rgba(255,140,0,0.2)',
            zerolinecolor='rgba(255,140,0,0.4)'
        ),
        yaxis=dict(
            gridcolor='rgba(255,140,0,0.2)',
            zerolinecolor='rgba(255,140,0,0.4)'
        )
    )
    
    return fig
