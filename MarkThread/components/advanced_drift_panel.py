"""
Advanced drift visualization component for WordThread Marker-Engine
Multi-axis analysis and temporal patterns beyond basic drift detection
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

from utils.performance import performance_monitor


def render_advanced_drift_panel(analysis_data: Optional[Dict], sqlite_data: Optional[Dict]):
    """Render advanced drift analysis with multi-axis and temporal patterns"""
    
    st.markdown("### 📈 Advanced Drift Analysis")
    st.markdown("Multi-dimensional drift detection with temporal patterns, statistical analysis, and predictive insights.")
    
    # Extract and prepare drift data
    drift_data = extract_drift_data(analysis_data, sqlite_data)
    
    if not drift_data or len(drift_data) == 0:
        render_no_drift_data_message()
        return
    
    # Advanced control panel
    render_drift_controls(drift_data)
    
    # Main analysis tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Multi-Axis Analysis", 
        "⏱️ Temporal Patterns", 
        "📊 Statistical Analysis", 
        "🔮 Predictive Insights",
        "🎯 Anomaly Detection"
    ])
    
    with tab1:
        render_multi_axis_analysis(drift_data)
    
    with tab2:
        render_temporal_patterns(drift_data)
    
    with tab3:
        render_statistical_analysis(drift_data)
    
    with tab4:
        render_predictive_insights(drift_data)
    
    with tab5:
        render_anomaly_detection(drift_data)


def extract_drift_data(analysis_data: Optional[Dict], sqlite_data: Optional[Dict]) -> List[Dict]:
    """Extract and prepare drift data from available sources"""
    
    drift_records = []
    
    # Extract from AnalysisBundle
    if analysis_data and 'hits' in analysis_data:
        hits_df = pd.DataFrame(analysis_data['hits'])
        
        if not hits_df.empty and 'ts' in hits_df.columns and 'marker_id' in hits_df.columns:
            # Group by time windows for drift calculation
            hits_df['datetime'] = pd.to_datetime(hits_df['ts'], unit='s')
            hits_df['hour'] = hits_df['datetime'].dt.floor('H')
            
            # Calculate drift metrics per marker per hour
            for marker_id in hits_df['marker_id'].unique():
                marker_data = hits_df[hits_df['marker_id'] == marker_id]
                
                hourly_counts = marker_data.groupby('hour').size().reset_index()
                hourly_counts.columns = ['timestamp', 'hit_count']
                
                for i, row in hourly_counts.iterrows():
                    record = {
                        'timestamp': row['timestamp'].timestamp(),
                        'marker_id': marker_id,
                        'hit_count': row['hit_count'],
                        'metric_type': 'hit_frequency',
                        'value': row['hit_count'],
                        'source': 'analysis_bundle',
                        'metadata': {
                            'window_size': '1h',
                            'aggregation': 'count'
                        }
                    }
                    drift_records.append(record)
    
    # Extract from SQLite data
    if sqlite_data and 'drift_metrics' in sqlite_data:
        sqlite_drift = sqlite_data['drift_metrics']
        for drift in sqlite_drift:
            record = {
                'timestamp': drift.get('timestamp', datetime.now().timestamp()),
                'marker_id': drift.get('marker_id'),
                'hit_count': drift.get('hit_count', 0),
                'metric_type': drift.get('metric_type', 'drift_score'),
                'value': drift.get('drift_value', 0.0),
                'source': 'sqlite',
                'metadata': drift.get('metadata', {})
            }
            drift_records.append(record)
    
    # Generate synthetic data if none available (for demonstration)
    if not drift_records:
        st.session_state.using_synthetic_drift = True
        drift_records = generate_synthetic_drift_data()
    else:
        st.session_state.using_synthetic_drift = False
    
    return drift_records


def generate_synthetic_drift_data() -> List[Dict]:
    """Generate synthetic drift data for demonstration purposes"""
    
    synthetic_data = []
    base_time = datetime.now().timestamp() - (7 * 24 * 3600)  # 7 days ago
    
    markers = ['marker_001', 'marker_002', 'marker_003', 'marker_004', 'marker_005']
    metric_types = ['hit_frequency', 'drift_score', 'confidence_drift', 'temporal_variance']
    
    for i in range(168):  # 7 days * 24 hours
        timestamp = base_time + (i * 3600)  # hourly data
        
        for marker_id in markers:
            for metric_type in metric_types:
                # Create realistic drift patterns
                base_value = 10 + np.sin(i * 2 * np.pi / 24) * 3  # Daily cycle
                weekly_trend = np.sin(i * 2 * np.pi / 168) * 2    # Weekly cycle
                noise = np.random.normal(0, 1)
                
                # Add drift events
                if i > 50 and i < 70:  # Drift event
                    drift_factor = 2.5
                elif i > 120 and i < 130:  # Another drift event
                    drift_factor = 0.3
                else:
                    drift_factor = 1.0
                
                value = (base_value + weekly_trend + noise) * drift_factor
                
                # Ensure positive values
                value = max(0.1, value)
                
                # Special handling for different metric types
                if metric_type == 'drift_score':
                    value = min(1.0, max(0.0, value / 20))  # Normalize to [0,1]
                elif metric_type == 'confidence_drift':
                    value = min(1.0, max(0.0, 0.8 + noise * 0.1))  # High base confidence
                elif metric_type == 'temporal_variance':
                    value = max(0.01, abs(noise) * 0.5)  # Always positive variance
                
                record = {
                    'timestamp': timestamp,
                    'marker_id': marker_id,
                    'hit_count': int(value) if metric_type == 'hit_frequency' else int(base_value),
                    'metric_type': metric_type,
                    'value': value,
                    'source': 'synthetic',
                    'metadata': {
                        'window_size': '1h',
                        'aggregation': 'mean',
                        'confidence': 0.7 + np.random.random() * 0.2
                    }
                }
                synthetic_data.append(record)
    
    return synthetic_data


def render_no_drift_data_message():
    """Render message when no drift data is available"""
    
    st.info("📈 No drift data found in the current dataset.")
    
    with st.expander("📚 About Advanced Drift Analysis"):
        st.markdown("""
        **Advanced Drift Analysis** provides multi-dimensional insights into temporal patterns and changes:
        
        **Multi-Axis Analysis:**
        - Frequency drift across multiple markers simultaneously
        - Cross-correlation between different drift metrics
        - Principal component analysis of drift patterns
        
        **Temporal Patterns:**
        - Cyclic pattern detection (daily, weekly, monthly)
        - Trend analysis with statistical significance testing
        - Change point detection and segmentation
        
        **Statistical Analysis:**
        - Distribution analysis of drift magnitudes
        - Confidence intervals and statistical tests
        - Outlier detection and significance assessment
        
        **Predictive Insights:**
        - Drift forecasting using time series models
        - Early warning indicators
        - Risk assessment and mitigation suggestions
        
        Upload data with temporal marker patterns to see detailed analysis.
        """)


def render_drift_controls(drift_data: List[Dict]):
    """Render advanced control panel for drift analysis"""
    
    st.markdown("#### 🎛️ Analysis Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Marker selection
        all_markers = list(set(item['marker_id'] for item in drift_data if item['marker_id']))
        selected_markers = st.multiselect(
            "Select Markers",
            options=all_markers,
            default=all_markers[:5] if len(all_markers) > 5 else all_markers,
            key="drift_marker_filter"
        )
    
    with col2:
        # Metric type selection
        all_metrics = list(set(item['metric_type'] for item in drift_data))
        selected_metrics = st.multiselect(
            "Drift Metrics",
            options=all_metrics,
            default=all_metrics,
            key="drift_metric_filter"
        )
    
    with col3:
        # Time window selection
        window_options = ['1H', '6H', '1D', '1W']
        selected_window = st.selectbox(
            "Analysis Window",
            options=window_options,
            index=2,  # Default to 1D
            key="drift_window_filter"
        )
    
    with col4:
        # Statistical significance level
        significance_level = st.slider(
            "Significance Level",
            min_value=0.01,
            max_value=0.10,
            value=0.05,
            step=0.01,
            key="significance_level"
        )
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            smoothing_enabled = st.checkbox("Enable Smoothing", value=True, key="smoothing_enabled")
            smoothing_window = 6  # Default value
            if smoothing_enabled:
                smoothing_window = st.slider("Smoothing Window", 1, 24, 6, key="smoothing_window")
        
        with col2:
            anomaly_threshold = st.slider(
                "Anomaly Threshold (σ)",
                min_value=1.0,
                max_value=4.0,
                value=2.0,
                step=0.1,
                key="anomaly_threshold"
            )
        
        with col3:
            forecast_horizon = st.slider(
                "Forecast Horizon (hours)",
                min_value=1,
                max_value=168,  # 1 week
                value=24,
                key="forecast_horizon"
            )
    
    # Store filters in session state
    st.session_state.drift_filters = {
        'markers': selected_markers,
        'metrics': selected_metrics,
        'window': selected_window,
        'significance': significance_level,
        'smoothing_enabled': smoothing_enabled,
        'smoothing_window': smoothing_window,
        'anomaly_threshold': anomaly_threshold,
        'forecast_horizon': forecast_horizon
    }


def render_multi_axis_analysis(drift_data: List[Dict]):
    """Render multi-axis drift analysis"""
    
    st.markdown("#### 🔍 Multi-Axis Drift Analysis")
    
    # Show demo mode banner if using synthetic data
    if getattr(st.session_state, 'using_synthetic_drift', False):
        st.warning("🧪 **Demo Mode**: Using synthetic drift data for demonstration. Upload real data to see actual analysis.")
    
    filtered_data = apply_drift_filters(drift_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_multi_marker_comparison(filtered_data)
    
    with col2:
        render_metric_correlation_matrix(filtered_data)
    
    # Cross-dimensional analysis
    render_pca_analysis(filtered_data)
    
    # Drift magnitude heatmap
    render_drift_heatmap(filtered_data)


def render_multi_marker_comparison(data: List[Dict]):
    """Render multi-marker drift comparison"""
    
    st.markdown("##### 📊 Multi-Marker Comparison")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    
    if df.empty:
        st.info("No data available for comparison")
        return
    
    # Create subplot for multiple markers
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, marker_id in enumerate(df['marker_id'].unique()):
        marker_data = df[df['marker_id'] == marker_id]
        
        # Group by metric type and calculate mean value
        metric_data = marker_data.groupby(['datetime', 'metric_type'])['value'].mean().reset_index()
        
        for metric_type in metric_data['metric_type'].unique():
            type_data = metric_data[metric_data['metric_type'] == metric_type]
            
            fig.add_trace(go.Scatter(
                x=type_data['datetime'],
                y=type_data['value'],
                mode='lines+markers',
                name=f"{marker_id} - {metric_type}",
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{marker_id}</b><br>" +
                              f"Metric: {metric_type}<br>" +
                              "Time: %{x}<br>" +
                              "Value: %{y:.3f}<br>" +
                              "<extra></extra>"
            ))
    
    fig.update_layout(
        title="Multi-Marker Drift Comparison",
        xaxis_title="Time",
        yaxis_title="Drift Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_metric_correlation_matrix(data: List[Dict]):
    """Render correlation matrix between different drift metrics"""
    
    st.markdown("##### 🔗 Metric Correlation Matrix")
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("No data available for correlation analysis")
        return
    
    # Pivot data to create correlation matrix
    pivot_df = df.pivot_table(
        index=['timestamp', 'marker_id'],
        columns='metric_type',
        values='value',
        aggfunc='mean'
    ).reset_index()
    
    # Calculate correlation matrix
    numeric_columns = pivot_df.select_dtypes(include=[np.number]).columns
    numeric_columns = [col for col in numeric_columns if col not in ['timestamp']]
    
    if len(numeric_columns) > 1:
        correlation_matrix = pivot_df[numeric_columns].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Drift Metrics Correlation",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient metrics for correlation analysis")


def render_pca_analysis(data: List[Dict]):
    """Render Principal Component Analysis of drift patterns"""
    
    st.markdown("##### 🎯 Principal Component Analysis")
    
    df = pd.DataFrame(data)
    
    if df.empty or len(df) < 10:
        st.info("Insufficient data for PCA analysis")
        return
    
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        
        # Prepare data for PCA
        pivot_df = df.pivot_table(
            index=['timestamp'],
            columns=['marker_id', 'metric_type'],
            values='value',
            aggfunc='mean'
        ).fillna(0)
        
        if pivot_df.shape[1] < 2:
            st.info("Need more markers/metrics for meaningful PCA")
            return
        
        # Standardize the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(pivot_df.values)
        
        # Apply PCA
        pca = PCA(n_components=min(3, scaled_data.shape[1]))
        pca_result = pca.fit_transform(scaled_data)
        
        # Create PCA visualization
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=pca_result[:, 0],
            y=pca_result[:, 1],
            mode='markers+lines',
            marker=dict(size=6, color=list(range(len(pca_result))), colorscale='Viridis'),
            name='Drift Trajectory',
            hovertemplate="PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>Time: %{text}<extra></extra>",
            text=[pd.to_datetime(ts, unit='s').strftime('%Y-%m-%d %H:%M') for ts in pivot_df.index]
        ))
        
        fig.update_layout(
            title=f"PCA of Drift Patterns (Explained Variance: {pca.explained_variance_ratio_[:2].sum():.1%})",
            xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]:.1%})",
            yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]:.1%})",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show component loadings
        with st.expander("📊 Component Loadings"):
            loadings_df = pd.DataFrame(
                pca.components_[:2].T,
                columns=['PC1', 'PC2'],
                index=pivot_df.columns
            )
            st.dataframe(loadings_df.round(3), use_container_width=True)
            
    except ImportError:
        st.warning("🔧 PCA analysis requires scikit-learn. Install it to enable this feature.")
    except Exception as e:
        st.error(f"PCA analysis failed: {str(e)}")


def render_drift_heatmap(data: List[Dict]):
    """Render drift magnitude heatmap"""
    
    st.markdown("##### 🔥 Drift Magnitude Heatmap")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['hour'] = df['datetime'].dt.hour
    df['day'] = df['datetime'].dt.day_name()
    
    if df.empty:
        st.info("No data available for heatmap")
        return
    
    # Create heatmap data
    heatmap_data = df.groupby(['day', 'hour'])['value'].mean().reset_index()
    heatmap_pivot = heatmap_data.pivot(index='day', columns='hour', values='value').fillna(0)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_pivot.reindex([day for day in day_order if day in heatmap_pivot.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate="Day: %{y}<br>Hour: %{x}<br>Avg Drift: %{z:.3f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Drift Patterns by Day and Hour",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_temporal_patterns(drift_data: List[Dict]):
    """Render temporal pattern analysis"""
    
    st.markdown("#### ⏱️ Temporal Pattern Analysis")
    
    filtered_data = apply_drift_filters(drift_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_cyclic_patterns(filtered_data)
    
    with col2:
        render_trend_analysis(filtered_data)
    
    # Change point detection
    render_change_point_detection(filtered_data)
    
    # Seasonality decomposition
    render_seasonality_decomposition(filtered_data)


def render_cyclic_patterns(data: List[Dict]):
    """Render cyclic pattern detection"""
    
    st.markdown("##### 🔄 Cyclic Pattern Detection")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    
    if df.empty:
        st.info("No data available for cyclic analysis")
        return
    
    # Calculate different time cycles
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_of_week
    df['day_of_month'] = df['datetime'].dt.day
    
    cycles = {
        'Daily (Hour)': ('hour', range(24)),
        'Weekly (Day)': ('day_of_week', range(7)),
        'Monthly (Day)': ('day_of_month', range(1, 32))
    }
    
    selected_cycle = st.selectbox("Select Cycle", list(cycles.keys()), key="cycle_selection")
    cycle_col, cycle_range = cycles[selected_cycle]
    
    # Aggregate data by cycle
    cycle_data = df.groupby(cycle_col)['value'].agg(['mean', 'std', 'count']).reset_index()
    
    fig = go.Figure()
    
    # Mean line
    fig.add_trace(go.Scatter(
        x=cycle_data[cycle_col],
        y=cycle_data['mean'],
        mode='lines+markers',
        name='Mean',
        line=dict(color='#FFD700', width=3),
        marker=dict(size=8)
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=cycle_data[cycle_col],
        y=cycle_data['mean'] + cycle_data['std'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=cycle_data[cycle_col],
        y=cycle_data['mean'] - cycle_data['std'],
        mode='lines',
        line=dict(width=0),
        fillcolor='rgba(255, 215, 0, 0.2)',
        fill='tonexty',
        name='±1 Std Dev',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"{selected_cycle} Pattern",
        xaxis_title=cycle_col.replace('_', ' ').title(),
        yaxis_title="Average Drift Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_trend_analysis(data: List[Dict]):
    """Render statistical trend analysis"""
    
    st.markdown("##### 📈 Trend Analysis")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if df.empty or len(df) < 10:
        st.info("Insufficient data for trend analysis")
        return
    
    # Perform trend analysis using linear regression
    time_numeric = (df['datetime'] - df['datetime'].min()).dt.total_seconds()
    slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, df['value'])
    
    # Create trend visualization
    fig = go.Figure()
    
    # Original data
    fig.add_trace(go.Scatter(
        x=df['datetime'],
        y=df['value'],
        mode='markers',
        name='Data Points',
        marker=dict(size=4, color='#FF8C00', opacity=0.6)
    ))
    
    # Trend line
    trend_line = intercept + slope * time_numeric
    fig.add_trace(go.Scatter(
        x=df['datetime'],
        y=trend_line,
        mode='lines',
        name=f'Trend (r²={r_value**2:.3f})',
        line=dict(color='#FFD700', width=3)
    ))
    
    fig.update_layout(
        title="Statistical Trend Analysis",
        xaxis_title="Time",
        yaxis_title="Drift Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        trend_direction = "Increasing" if slope > 0 else "Decreasing" if slope < 0 else "Stable"
        st.metric("Trend Direction", trend_direction)
    
    with col2:
        st.metric("Slope", f"{slope:.6f}")
    
    with col3:
        significance = "Significant" if p_value < 0.05 else "Not Significant"
        st.metric("Statistical Significance", significance)


def render_change_point_detection(data: List[Dict]):
    """Render change point detection analysis"""
    
    st.markdown("##### 🎯 Change Point Detection")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if df.empty or len(df) < 20:
        st.info("Insufficient data for change point detection")
        return
    
    # Simple change point detection using rolling statistics
    window = min(24, len(df) // 4)  # Adaptive window size
    df['rolling_mean'] = df['value'].rolling(window=window, center=True).mean()
    df['rolling_std'] = df['value'].rolling(window=window, center=True).std()
    
    # Detect significant changes in mean
    df['mean_change'] = df['rolling_mean'].diff().abs()
    df['std_change'] = df['rolling_std'].diff().abs()
    
    # Find change points (peaks in change magnitude)
    if len(df) > 10:
        mean_peaks, _ = find_peaks(df['mean_change'].fillna(0), height=df['mean_change'].std())
        std_peaks, _ = find_peaks(df['std_change'].fillna(0), height=df['std_change'].std())
        
        fig = go.Figure()
        
        # Original data
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['value'],
            mode='lines+markers',
            name='Drift Values',
            line=dict(color='#FF8C00', width=2),
            marker=dict(size=4)
        ))
        
        # Rolling mean
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['rolling_mean'],
            mode='lines',
            name='Rolling Mean',
            line=dict(color='#FFD700', width=2)
        ))
        
        # Mark change points
        if len(mean_peaks) > 0:
            change_points = df.iloc[mean_peaks]
            fig.add_trace(go.Scatter(
                x=change_points['datetime'],
                y=change_points['value'],
                mode='markers',
                name='Change Points',
                marker=dict(size=12, color='red', symbol='diamond'),
                hovertemplate="Change Point<br>Time: %{x}<br>Value: %{y:.3f}<extra></extra>"
            ))
        
        fig.update_layout(
            title=f"Change Point Detection ({len(mean_peaks)} points found)",
            xaxis_title="Time",
            yaxis_title="Drift Value",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display change point summary
        if len(mean_peaks) > 0:
            st.markdown("**Detected Change Points:**")
            change_summary = []
            for peak in mean_peaks:
                change_summary.append({
                    'Time': df.iloc[peak]['datetime'].strftime('%Y-%m-%d %H:%M'),
                    'Value': f"{df.iloc[peak]['value']:.3f}",
                    'Change Magnitude': f"{df.iloc[peak]['mean_change']:.3f}"
                })
            
            st.table(pd.DataFrame(change_summary))
    else:
        st.info("Not enough data points for reliable change point detection")


def render_seasonality_decomposition(data: List[Dict]):
    """Render seasonality decomposition analysis"""
    
    st.markdown("##### 🌊 Seasonality Decomposition")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime').set_index('datetime')
    
    if df.empty or len(df) < 48:  # Need at least 2 days of hourly data
        st.info("Insufficient data for seasonality decomposition (need at least 48 hours)")
        return
    
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # Resample to hourly frequency and fill missing values
        hourly_data = df['value'].resample('H').mean().fillna(method='forward').fillna(method='backward')
        
        if len(hourly_data) < 48:
            st.info("Need at least 48 hours of data for seasonality analysis")
            return
        
        # Perform seasonal decomposition
        decomposition = seasonal_decompose(hourly_data, model='additive', period=24)
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=['Original', 'Trend', 'Seasonal', 'Residual'],
            vertical_spacing=0.08
        )
        
        # Original data
        fig.add_trace(go.Scatter(
            x=hourly_data.index,
            y=hourly_data.values,
            mode='lines',
            name='Original',
            line=dict(color='#FF8C00')
        ), row=1, col=1)
        
        # Trend
        fig.add_trace(go.Scatter(
            x=decomposition.trend.index,
            y=decomposition.trend.values,
            mode='lines',
            name='Trend',
            line=dict(color='#FFD700')
        ), row=2, col=1)
        
        # Seasonal
        fig.add_trace(go.Scatter(
            x=decomposition.seasonal.index,
            y=decomposition.seasonal.values,
            mode='lines',
            name='Seasonal',
            line=dict(color='#32CD32')
        ), row=3, col=1)
        
        # Residual
        fig.add_trace(go.Scatter(
            x=decomposition.resid.index,
            y=decomposition.resid.values,
            mode='lines',
            name='Residual',
            line=dict(color='#FF6347')
        ), row=4, col=1)
        
        fig.update_layout(
            title="Seasonal Decomposition",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.warning("🔧 Seasonality analysis requires statsmodels. Install it to enable this feature.")
    except Exception as e:
        st.error(f"Seasonality decomposition failed: {str(e)}")


def render_statistical_analysis(drift_data: List[Dict]):
    """Render statistical analysis of drift patterns"""
    
    st.markdown("#### 📊 Statistical Analysis")
    
    filtered_data = apply_drift_filters(drift_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_distribution_analysis(filtered_data)
    
    with col2:
        render_confidence_intervals(filtered_data)
    
    # Statistical tests
    render_statistical_tests(filtered_data)
    
    # Outlier analysis
    render_outlier_analysis(filtered_data)


def render_distribution_analysis(data: List[Dict]):
    """Render distribution analysis of drift values"""
    
    st.markdown("##### 📈 Distribution Analysis")
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("No data available for distribution analysis")
        return
    
    values = df['value'].dropna()
    
    if len(values) == 0:
        st.info("No valid values for distribution analysis")
        return
    
    # Create histogram with statistical overlay
    fig = go.Figure()
    
    # Histogram
    fig.add_trace(go.Histogram(
        x=values,
        nbinsx=30,
        name='Distribution',
        marker_color='#FF8C00',
        opacity=0.7,
        histnorm='probability density'
    ))
    
    # Normal distribution overlay
    x_range = np.linspace(values.min(), values.max(), 100)
    normal_dist = stats.norm.pdf(x_range, values.mean(), values.std())
    
    fig.add_trace(go.Scatter(
        x=x_range,
        y=normal_dist,
        mode='lines',
        name='Normal Fit',
        line=dict(color='#FFD700', width=3)
    ))
    
    fig.update_layout(
        title="Drift Value Distribution",
        xaxis_title="Drift Value",
        yaxis_title="Density",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mean", f"{values.mean():.3f}")
    
    with col2:
        st.metric("Std Dev", f"{values.std():.3f}")
    
    with col3:
        st.metric("Skewness", f"{stats.skew(values):.3f}")
    
    with col4:
        st.metric("Kurtosis", f"{stats.kurtosis(values):.3f}")


def render_confidence_intervals(data: List[Dict]):
    """Render confidence interval analysis"""
    
    st.markdown("##### 📏 Confidence Intervals")
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("No data available for confidence analysis")
        return
    
    # Group by marker and calculate confidence intervals
    markers = df['marker_id'].unique()
    confidence_data = []
    
    for marker in markers:
        marker_data = df[df['marker_id'] == marker]['value'].dropna()
        
        if len(marker_data) > 1:
            mean_val = marker_data.mean()
            std_err = stats.sem(marker_data)
            ci_95 = stats.t.interval(0.95, len(marker_data)-1, loc=mean_val, scale=std_err)
            ci_99 = stats.t.interval(0.99, len(marker_data)-1, loc=mean_val, scale=std_err)
            
            confidence_data.append({
                'Marker': marker,
                'Mean': mean_val,
                'CI_95_Lower': ci_95[0],
                'CI_95_Upper': ci_95[1],
                'CI_99_Lower': ci_99[0],
                'CI_99_Upper': ci_99[1],
                'Sample_Size': len(marker_data)
            })
    
    if confidence_data:
        ci_df = pd.DataFrame(confidence_data)
        
        # Create confidence interval plot
        fig = go.Figure()
        
        # 99% CI
        fig.add_trace(go.Scatter(
            x=ci_df['Marker'],
            y=ci_df['CI_99_Upper'],
            mode='markers',
            marker=dict(symbol='triangle-up', size=8, color='#FF6347'),
            name='99% CI Upper',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=ci_df['Marker'],
            y=ci_df['CI_99_Lower'],
            mode='markers',
            marker=dict(symbol='triangle-down', size=8, color='#FF6347'),
            name='99% CI Lower',
            fill='tonexty',
            fillcolor='rgba(255, 99, 71, 0.1)'
        ))
        
        # 95% CI
        fig.add_trace(go.Scatter(
            x=ci_df['Marker'],
            y=ci_df['CI_95_Upper'],
            mode='markers',
            marker=dict(symbol='triangle-up', size=8, color='#FFD700'),
            name='95% CI Upper',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=ci_df['Marker'],
            y=ci_df['CI_95_Lower'],
            mode='markers',
            marker=dict(symbol='triangle-down', size=8, color='#FFD700'),
            name='95% CI Lower',
            fill='tonexty',
            fillcolor='rgba(255, 215, 0, 0.2)'
        ))
        
        # Mean values
        fig.add_trace(go.Scatter(
            x=ci_df['Marker'],
            y=ci_df['Mean'],
            mode='markers',
            marker=dict(size=10, color='#FF8C00', symbol='diamond'),
            name='Mean',
            hovertemplate="Marker: %{x}<br>Mean: %{y:.3f}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Confidence Intervals by Marker",
            xaxis_title="Marker ID",
            yaxis_title="Drift Value",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display confidence interval table
        st.dataframe(ci_df.round(3), use_container_width=True)
    else:
        st.info("Insufficient data for confidence interval calculation")


def render_statistical_tests(data: List[Dict]):
    """Render statistical significance tests"""
    
    st.markdown("##### 🔬 Statistical Tests")
    
    df = pd.DataFrame(data)
    
    if df.empty or len(df) < 10:
        st.info("Insufficient data for statistical tests")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Normality Tests:**")
        
        values = df['value'].dropna()
        
        # Shapiro-Wilk test (for smaller samples)
        if len(values) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(values)
            st.write(f"Shapiro-Wilk: p = {shapiro_p:.4f}")
            if shapiro_p < 0.05:
                st.write("❌ Not normally distributed")
            else:
                st.write("✅ Normally distributed")
        
        # Kolmogorov-Smirnov test
        ks_stat, ks_p = stats.kstest(values, 'norm', args=(values.mean(), values.std()))
        st.write(f"Kolmogorov-Smirnov: p = {ks_p:.4f}")
        if ks_p < 0.05:
            st.write("❌ Not normally distributed")
        else:
            st.write("✅ Normally distributed")
    
    with col2:
        st.markdown("**Stationarity Tests:**")
        
        # Simple stationarity check using rolling statistics
        window = min(24, len(df) // 4)
        df_sorted = df.sort_values('timestamp')
        rolling_mean = df_sorted['value'].rolling(window=window).mean()
        rolling_std = df_sorted['value'].rolling(window=window).std()
        
        # Check if rolling statistics are relatively stable
        mean_stability = rolling_mean.std() / rolling_mean.mean() if rolling_mean.mean() != 0 else 0
        std_stability = rolling_std.std() / rolling_std.mean() if rolling_std.mean() != 0 else 0
        
        st.write(f"Mean stability: {mean_stability:.3f}")
        st.write(f"Std stability: {std_stability:.3f}")
        
        if mean_stability < 0.1 and std_stability < 0.1:
            st.write("✅ Relatively stationary")
        else:
            st.write("❌ Non-stationary")


def render_outlier_analysis(data: List[Dict]):
    """Render outlier detection and analysis"""
    
    st.markdown("##### 🎯 Outlier Analysis")
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("No data available for outlier analysis")
        return
    
    values = df['value'].dropna()
    
    if len(values) == 0:
        st.info("No valid values for outlier analysis")
        return
    
    # Calculate outliers using IQR method
    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = values[(values < lower_bound) | (values > upper_bound)]
    
    # Calculate outliers using Z-score method
    z_scores = np.abs(stats.zscore(values))
    z_outliers = values[z_scores > 2]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Points", len(values))
    
    with col2:
        st.metric("IQR Outliers", len(outliers))
    
    with col3:
        st.metric("Z-Score Outliers", len(z_outliers))
    
    with col4:
        outlier_percentage = (len(outliers) / len(values)) * 100
        st.metric("Outlier %", f"{outlier_percentage:.1f}%")
    
    # Box plot with outliers
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=values,
        name='Drift Values',
        marker_color='#FF8C00',
        boxpoints='outliers'
    ))
    
    fig.update_layout(
        title="Outlier Detection (Box Plot)",
        yaxis_title="Drift Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_predictive_insights(drift_data: List[Dict]):
    """Render predictive analysis and forecasting"""
    
    st.markdown("#### 🔮 Predictive Insights")
    
    filtered_data = apply_drift_filters(drift_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_drift_forecasting(filtered_data)
    
    with col2:
        render_early_warning_indicators(filtered_data)
    
    # Risk assessment
    render_risk_assessment(filtered_data)


def render_drift_forecasting(data: List[Dict]):
    """Render drift forecasting using time series models"""
    
    st.markdown("##### 🔮 Drift Forecasting")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if df.empty or len(df) < 10:
        st.info("Insufficient data for forecasting")
        return
    
    # Simple linear extrapolation
    time_numeric = (df['datetime'] - df['datetime'].min()).dt.total_seconds()
    slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, df['value'])
    
    # Generate forecast
    filters = st.session_state.get('drift_filters', {})
    forecast_hours = filters.get('forecast_horizon', 24)
    
    last_time = df['datetime'].max()
    forecast_times = pd.date_range(last_time, periods=forecast_hours+1, freq='H')[1:]
    
    forecast_time_numeric = (forecast_times - df['datetime'].min()).total_seconds()
    forecast_values = intercept + slope * forecast_time_numeric
    
    # Calculate prediction intervals (simplified)
    prediction_std = np.sqrt(std_err**2 * (1 + 1/len(df) + 
                                         (forecast_time_numeric - time_numeric.mean())**2 / 
                                         ((time_numeric - time_numeric.mean())**2).sum()))
    
    upper_bound = forecast_values + 1.96 * prediction_std
    lower_bound = forecast_values - 1.96 * prediction_std
    
    # Create forecast plot
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=df['datetime'],
        y=df['value'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='#FF8C00', width=2),
        marker=dict(size=4)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_times,
        y=forecast_values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#FFD700', width=2, dash='dash'),
        marker=dict(size=4)
    ))
    
    # Prediction interval
    fig.add_trace(go.Scatter(
        x=forecast_times,
        y=upper_bound,
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_times,
        y=lower_bound,
        mode='lines',
        line=dict(width=0),
        fillcolor='rgba(255, 215, 0, 0.2)',
        fill='tonexty',
        name='95% Prediction Interval',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"Drift Forecast ({forecast_hours}h horizon)",
        xaxis_title="Time",
        yaxis_title="Drift Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Forecast summary
    col1, col2 = st.columns(2)
    
    with col1:
        trend_direction = "Increasing" if slope > 0 else "Decreasing"
        st.metric("Forecast Trend", trend_direction)
    
    with col2:
        confidence = max(0, min(100, (r_value**2) * 100))
        st.metric("Model Confidence", f"{confidence:.1f}%")


def render_early_warning_indicators(data: List[Dict]):
    """Render early warning indicators for drift events"""
    
    st.markdown("##### ⚠️ Early Warning Indicators")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if df.empty or len(df) < 10:
        st.info("Insufficient data for warning indicators")
        return
    
    # Calculate warning indicators
    window = min(12, len(df) // 3)  # Adaptive window
    df['rolling_mean'] = df['value'].rolling(window=window).mean()
    df['rolling_std'] = df['value'].rolling(window=window).std()
    df['z_score'] = (df['value'] - df['rolling_mean']) / df['rolling_std']
    
    # Current status
    latest_z = df['z_score'].iloc[-1] if not pd.isna(df['z_score'].iloc[-1]) else 0
    latest_std = df['rolling_std'].iloc[-1] if not pd.isna(df['rolling_std'].iloc[-1]) else 0
    recent_trend = df['value'].tail(6).diff().mean()  # 6-period trend
    
    # Warning levels
    warnings = []
    
    if abs(latest_z) > 2:
        warnings.append(f"⚠️ High Z-score: {latest_z:.2f}")
    
    if latest_std > df['rolling_std'].quantile(0.9):
        warnings.append("⚠️ High variability detected")
    
    if abs(recent_trend) > df['value'].std() * 0.5:
        direction = "increasing" if recent_trend > 0 else "decreasing"
        warnings.append(f"⚠️ Strong {direction} trend")
    
    # Display warnings
    if warnings:
        st.error("🚨 **Warning Indicators Active:**")
        for warning in warnings:
            st.write(warning)
    else:
        st.success("✅ No warning indicators active")
    
    # Warning indicator chart
    fig = go.Figure()
    
    # Z-score
    fig.add_trace(go.Scatter(
        x=df['datetime'],
        y=df['z_score'],
        mode='lines',
        name='Z-Score',
        line=dict(color='#FF8C00', width=2)
    ))
    
    # Warning thresholds
    fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Warning (+2σ)")
    fig.add_hline(y=-2, line_dash="dash", line_color="red", annotation_text="Warning (-2σ)")
    
    fig.update_layout(
        title="Early Warning Z-Score Monitoring",
        xaxis_title="Time",
        yaxis_title="Z-Score",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_risk_assessment(data: List[Dict]):
    """Render comprehensive risk assessment"""
    
    st.markdown("##### 🎯 Risk Assessment")
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("No data available for risk assessment")
        return
    
    # Calculate risk metrics
    values = df['value'].dropna()
    
    if len(values) == 0:
        st.info("No valid values for risk assessment")
        return
    
    # Risk calculations
    volatility = values.std()
    mean_value = values.mean()
    cv = volatility / mean_value if mean_value != 0 else 0  # Coefficient of variation
    
    # Value at Risk (VaR) - simplified
    var_95 = values.quantile(0.05)  # 5th percentile
    var_99 = values.quantile(0.01)  # 1st percentile
    
    # Maximum drawdown
    cumulative = values.cumsum()
    running_max = cumulative.expanding().max()
    drawdown = cumulative - running_max
    max_drawdown = drawdown.min()
    
    # Risk categorization
    if cv < 0.1:
        risk_level = "Low"
        risk_color = "green"
    elif cv < 0.3:
        risk_level = "Medium"
        risk_color = "orange"
    else:
        risk_level = "High"
        risk_color = "red"
    
    # Display risk metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Risk Level", risk_level)
    
    with col2:
        st.metric("Volatility", f"{volatility:.3f}")
    
    with col3:
        st.metric("VaR (95%)", f"{var_95:.3f}")
    
    with col4:
        st.metric("Max Drawdown", f"{max_drawdown:.3f}")
    
    # Risk recommendations
    st.markdown("**Risk Mitigation Recommendations:**")
    
    recommendations = []
    
    if cv > 0.3:
        recommendations.append("🔍 High volatility detected - consider implementing anomaly detection")
    
    if abs(max_drawdown) > volatility * 2:
        recommendations.append("📉 Large drawdowns observed - monitor for systematic drift")
    
    if var_95 < mean_value * 0.5:
        recommendations.append("⚠️ High downside risk - implement early warning thresholds")
    
    if len(recommendations) == 0:
        recommendations.append("✅ Risk levels appear manageable with current monitoring")
    
    for rec in recommendations:
        st.info(rec)


def render_anomaly_detection(drift_data: List[Dict]):
    """Render anomaly detection analysis"""
    
    st.markdown("#### 🎯 Anomaly Detection")
    
    filtered_data = apply_drift_filters(drift_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_statistical_anomalies(filtered_data)
    
    with col2:
        render_isolation_forest_anomalies(filtered_data)
    
    # Anomaly timeline
    render_anomaly_timeline(filtered_data)


def render_statistical_anomalies(data: List[Dict]):
    """Render statistical anomaly detection"""
    
    st.markdown("##### 📊 Statistical Anomalies")
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("No data available for anomaly detection")
        return
    
    values = df['value'].dropna()
    
    if len(values) < 10:
        st.info("Insufficient data for statistical anomaly detection")
        return
    
    # Z-score method
    filters = st.session_state.get('drift_filters', {})
    threshold = filters.get('anomaly_threshold', 2.0)
    
    z_scores = np.abs(stats.zscore(values))
    z_anomalies = z_scores > threshold
    
    # IQR method
    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    iqr_anomalies = (values < lower_bound) | (values > upper_bound)
    
    # Modified Z-score (more robust)
    median = values.median()
    mad = np.median(np.abs(values - median))
    modified_z_scores = 0.6745 * (values - median) / mad
    modified_anomalies = np.abs(modified_z_scores) > threshold
    
    # Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Z-Score Anomalies", f"{z_anomalies.sum()}")
    
    with col2:
        st.metric("IQR Anomalies", f"{iqr_anomalies.sum()}")
    
    with col3:
        st.metric("Modified Z Anomalies", f"{modified_anomalies.sum()}")
    
    # Anomaly scores plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(len(z_scores))),
        y=z_scores,
        mode='markers',
        name='Z-Scores',
        marker=dict(
            size=6,
            color=z_anomalies,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Anomaly")
        ),
        hovertemplate="Index: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))
    
    # Threshold line
    fig.add_hline(y=threshold, line_dash="dash", line_color="red", 
                  annotation_text=f"Threshold ({threshold}σ)")
    
    fig.update_layout(
        title="Statistical Anomaly Scores",
        xaxis_title="Data Point Index",
        yaxis_title="Z-Score",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_isolation_forest_anomalies(data: List[Dict]):
    """Render isolation forest anomaly detection"""
    
    st.markdown("##### 🌲 Isolation Forest Anomalies")
    
    df = pd.DataFrame(data)
    
    if df.empty or len(df) < 20:
        st.info("Insufficient data for Isolation Forest (need at least 20 points)")
        return
    
    try:
        from sklearn.ensemble import IsolationForest
        
        # Prepare features
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_of_week
        
        features = ['value', 'hour', 'day_of_week']
        feature_data = df[features].fillna(0)
        
        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(feature_data)
        anomaly_scores = iso_forest.score_samples(feature_data)
        
        df['anomaly'] = anomaly_labels == -1
        df['anomaly_score'] = anomaly_scores
        
        # Summary
        anomaly_count = df['anomaly'].sum()
        anomaly_percentage = (anomaly_count / len(df)) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("IF Anomalies", f"{anomaly_count}")
        
        with col2:
            st.metric("Anomaly Rate", f"{anomaly_percentage:.1f}%")
        
        # Anomaly score distribution
        fig = go.Figure()
        
        # Normal points
        normal_data = df[~df['anomaly']]
        fig.add_trace(go.Scatter(
            x=normal_data['datetime'],
            y=normal_data['anomaly_score'],
            mode='markers',
            name='Normal',
            marker=dict(size=6, color='#32CD32', opacity=0.7)
        ))
        
        # Anomalous points
        anomaly_data = df[df['anomaly']]
        if not anomaly_data.empty:
            fig.add_trace(go.Scatter(
                x=anomaly_data['datetime'],
                y=anomaly_data['anomaly_score'],
                mode='markers',
                name='Anomaly',
                marker=dict(size=10, color='#FF6347', symbol='x')
            ))
        
        fig.update_layout(
            title="Isolation Forest Anomaly Detection",
            xaxis_title="Time",
            yaxis_title="Anomaly Score",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.warning("🔧 Isolation Forest requires scikit-learn. Install it to enable this feature.")
    except Exception as e:
        st.error(f"Isolation Forest analysis failed: {str(e)}")


def render_anomaly_timeline(data: List[Dict]):
    """Render anomaly detection timeline"""
    
    st.markdown("##### ⏰ Anomaly Timeline")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if df.empty:
        st.info("No data available for anomaly timeline")
        return
    
    # Simple anomaly detection using rolling statistics
    window = min(24, len(df) // 4)
    df['rolling_mean'] = df['value'].rolling(window=window, center=True).mean()
    df['rolling_std'] = df['value'].rolling(window=window, center=True).std()
    df['z_score'] = (df['value'] - df['rolling_mean']) / df['rolling_std']
    
    filters = st.session_state.get('drift_filters', {})
    threshold = filters.get('anomaly_threshold', 2.0)
    
    df['is_anomaly'] = np.abs(df['z_score']) > threshold
    
    # Create timeline plot
    fig = go.Figure()
    
    # Normal data
    normal_data = df[~df['is_anomaly']]
    fig.add_trace(go.Scatter(
        x=normal_data['datetime'],
        y=normal_data['value'],
        mode='lines+markers',
        name='Normal',
        line=dict(color='#32CD32', width=2),
        marker=dict(size=4)
    ))
    
    # Anomalous data
    anomaly_data = df[df['is_anomaly']]
    if not anomaly_data.empty:
        fig.add_trace(go.Scatter(
            x=anomaly_data['datetime'],
            y=anomaly_data['value'],
            mode='markers',
            name='Anomaly',
            marker=dict(size=12, color='#FF6347', symbol='x'),
            hovertemplate="<b>ANOMALY</b><br>Time: %{x}<br>Value: %{y:.3f}<extra></extra>"
        ))
    
    fig.update_layout(
        title=f"Anomaly Detection Timeline ({anomaly_data.shape[0] if not anomaly_data.empty else 0} anomalies)",
        xaxis_title="Time",
        yaxis_title="Drift Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly summary table
    if not anomaly_data.empty:
        st.markdown("**Recent Anomalies:**")
        
        anomaly_summary = anomaly_data.tail(10)[['datetime', 'value', 'z_score']].copy()
        anomaly_summary['datetime'] = anomaly_summary['datetime'].dt.strftime('%Y-%m-%d %H:%M')
        anomaly_summary = anomaly_summary.round(3)
        
        st.dataframe(anomaly_summary, use_container_width=True, hide_index=True)


def apply_drift_filters(data: List[Dict]) -> List[Dict]:
    """Apply current filters to drift data"""
    
    if 'drift_filters' not in st.session_state:
        return data
    
    filters = st.session_state.drift_filters
    filtered_data = data
    
    # Marker filter
    if filters.get('markers'):
        filtered_data = [item for item in filtered_data if item['marker_id'] in filters['markers']]
    
    # Metric filter
    if filters.get('metrics'):
        filtered_data = [item for item in filtered_data if item['metric_type'] in filters['metrics']]
    
    return filtered_data