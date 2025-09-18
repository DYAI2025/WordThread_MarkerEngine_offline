import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import scipy.stats as stats

def render_drift_panel(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]):
    """Render drift analysis panel showing temporal changes in marker patterns"""
    
    st.markdown("### 📈 Drift Analysis")
    st.markdown("Analyze temporal changes and patterns in marker behavior over time.")
    
    if not analysis_data and not sqlite_data:
        st.info("📈 No data available for drift analysis. Please upload data files.")
        return
    
    # Prepare drift analysis data
    drift_data = prepare_drift_data(analysis_data, sqlite_data)
    
    if drift_data.empty:
        st.warning("⚠️ Insufficient data for drift analysis")
        return
    
    # Render drift analysis controls
    drift_config = render_drift_controls()
    
    # Render different types of drift analysis
    render_temporal_drift(drift_data, drift_config)
    render_pattern_drift(drift_data, drift_config)
    render_statistical_drift(drift_data, drift_config)
    render_drift_summary(drift_data)

def prepare_drift_data(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare data for drift analysis"""
    
    data_frames = []
    
    # Process analysis bundle data
    if analysis_data and 'hits' in analysis_data:
        hits_df = pd.DataFrame(analysis_data['hits'])
        
        if not hits_df.empty and 'ts' in hits_df.columns:
            hits_df['timestamp'] = pd.to_datetime(hits_df['ts'], unit='s')
            hits_df['source'] = 'analysis_bundle'
            data_frames.append(hits_df)
    
    # Process SQLite data
    if sqlite_data and 'tables' in sqlite_data and 'hits' in sqlite_data['tables']:
        sqlite_hits = pd.DataFrame(sqlite_data['tables']['hits'])
        
        if not sqlite_hits.empty and 'ts' in sqlite_hits.columns:
            sqlite_hits['timestamp'] = pd.to_datetime(sqlite_hits['ts'], unit='s')
            sqlite_hits['source'] = 'sqlite'
            data_frames.append(sqlite_hits)
    
    # Combine and enhance data
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        
        # Add time-based features for drift analysis
        combined_df = add_temporal_features(combined_df)
        
        return combined_df
    
    return pd.DataFrame()

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal features for drift analysis"""
    
    if 'timestamp' not in df.columns:
        return df
    
    # Add time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_of_week
    df['day_name'] = df['timestamp'].dt.day_name()
    df['week'] = df['timestamp'].dt.isocalendar().week
    df['month'] = df['timestamp'].dt.month
    df['date'] = df['timestamp'].dt.date
    
    # Add time periods for drift analysis
    df = df.sort_values('timestamp')
    
    # Calculate time-based windows
    min_time = df['timestamp'].min()
    max_time = df['timestamp'].max()
    time_span = max_time - min_time
    
    # Create time periods (quarters of the total time span)
    if time_span.total_seconds() > 0:
        quarter_duration = time_span / 4
        df['time_period'] = pd.cut(
            df['timestamp'],
            bins=4,
            labels=['Early', 'Mid-Early', 'Mid-Late', 'Late']
        )
    
    return df

def render_drift_controls():
    """Render drift analysis controls"""
    
    st.markdown("#### ⚙️ Analysis Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Time window selection
        time_window = st.selectbox(
            "Time Window",
            ["1 hour", "6 hours", "1 day", "1 week"],
            index=2,
            help="Select time window for drift detection"
        )
        
        # Convert to minutes for calculation
        window_map = {
            "1 hour": 60,
            "6 hours": 360,
            "1 day": 1440,
            "1 week": 10080
        }
        window_minutes = window_map[time_window]
    
    with col2:
        # Drift sensitivity
        sensitivity = st.slider(
            "Sensitivity",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Drift detection sensitivity (lower = more sensitive)"
        )
    
    with col3:
        # Minimum observations
        min_observations = st.slider(
            "Min Observations",
            min_value=5,
            max_value=100,
            value=20,
            help="Minimum observations per window for reliable drift detection"
        )
    
    return {
        'time_window': time_window,
        'window_minutes': window_minutes,
        'sensitivity': sensitivity,
        'min_observations': min_observations
    }

def render_temporal_drift(drift_data: pd.DataFrame, config: Dict[str, Any]):
    """Render temporal drift analysis"""
    
    st.markdown("#### ⏰ Temporal Drift")
    
    if 'timestamp' not in drift_data.columns or 'marker_id' not in drift_data.columns:
        st.error("Missing required columns for temporal drift analysis")
        return
    
    # Calculate drift metrics over time windows
    window_freq = f"{config['window_minutes']}T"  # Convert to pandas frequency
    
    # Group by time windows and marker types
    temporal_groups = drift_data.set_index('timestamp').groupby('marker_id').resample(window_freq).size()
    temporal_df = temporal_groups.reset_index()
    temporal_df.columns = ['marker_id', 'timestamp', 'count']
    
    # Filter out windows with insufficient data
    temporal_df = temporal_df[temporal_df['count'] >= config['min_observations']]
    
    if temporal_df.empty:
        st.warning(f"No sufficient data windows found. Try reducing minimum observations or increasing time window.")
        return
    
    # Calculate drift indicators
    drift_indicators = calculate_drift_indicators(temporal_df, config)
    
    # Create temporal drift visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Activity Over Time', 'Drift Indicators'],
        vertical_spacing=0.15
    )
    
    # Activity over time
    for marker in temporal_df['marker_id'].unique():
        marker_data = temporal_df[temporal_df['marker_id'] == marker]
        
        fig.add_trace(
            go.Scatter(
                x=marker_data['timestamp'],
                y=marker_data['count'],
                mode='lines+markers',
                name=marker,
                line=dict(width=2),
                opacity=0.7
            ),
            row=1, col=1
        )
    
    # Drift indicators
    if not drift_indicators.empty:
        fig.add_trace(
            go.Scatter(
                x=drift_indicators['timestamp'],
                y=drift_indicators['drift_score'],
                mode='lines+markers',
                name='Drift Score',
                line=dict(color='red', width=3),
                yaxis='y2'
            ),
            row=2, col=1
        )
        
        # Add drift threshold line
        threshold = config['sensitivity']
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Threshold ({threshold})",
            row=2, col=1
        )
    
    fig.update_layout(
        title=f"Temporal Drift Analysis ({config['time_window']} windows)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=600
    )
    
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Activity Count", row=1, col=1)
    fig.update_yaxes(title_text="Drift Score", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def render_pattern_drift(drift_data: pd.DataFrame, config: Dict[str, Any]):
    """Render pattern-based drift analysis"""
    
    st.markdown("#### 🔄 Pattern Drift")
    
    if 'time_period' not in drift_data.columns:
        st.warning("Time period information not available for pattern drift analysis")
        return
    
    # Calculate pattern changes across time periods
    pattern_changes = analyze_pattern_changes(drift_data)
    
    if pattern_changes.empty:
        st.info("No significant pattern changes detected")
        return
    
    # Visualize pattern changes
    col1, col2 = st.columns(2)
    
    with col1:
        # Marker distribution changes
        st.markdown("##### Marker Distribution Changes")
        
        distribution_pivot = drift_data.pivot_table(
            values='id',
            index='marker_id',
            columns='time_period',
            aggfunc='count',
            fill_value=0
        )
        
        # Calculate relative changes
        if len(distribution_pivot.columns) > 1:
            early_col = distribution_pivot.columns[0]
            late_col = distribution_pivot.columns[-1]
            
            distribution_pivot['change_%'] = (
                (distribution_pivot[late_col] - distribution_pivot[early_col]) / 
                (distribution_pivot[early_col] + 1) * 100
            ).round(2)
            
            # Create change visualization
            fig = go.Figure(data=[
                go.Bar(
                    y=distribution_pivot.index,
                    x=distribution_pivot['change_%'],
                    orientation='h',
                    marker=dict(
                        color=distribution_pivot['change_%'],
                        colorscale=[
                            [0, 'red'], [0.5, 'yellow'], [1, 'green']
                        ],
                        colorbar=dict(title="Change %")
                    )
                )
            ])
            
            fig.update_layout(
                title="Pattern Changes (%)",
                xaxis_title="Percentage Change",
                yaxis_title="Marker",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Activity pattern heatmap
        st.markdown("##### Activity Heatmap")
        
        if 'hour' in drift_data.columns:
            hourly_pattern = drift_data.pivot_table(
                values='id',
                index='time_period',
                columns='hour',
                aggfunc='count',
                fill_value=0
            )
            
            fig = go.Figure(data=go.Heatmap(
                z=hourly_pattern.values,
                x=hourly_pattern.columns,
                y=hourly_pattern.index,
                colorscale='OrRd',
                hoverongaps=False
            ))
            
            fig.update_layout(
                title="Hourly Activity by Time Period",
                xaxis_title="Hour of Day",
                yaxis_title="Time Period",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)

def render_statistical_drift(drift_data: pd.DataFrame, config: Dict[str, Any]):
    """Render statistical drift analysis"""
    
    st.markdown("#### 📊 Statistical Drift")
    
    if 'time_period' not in drift_data.columns:
        return
    
    # Perform statistical tests for drift detection
    statistical_results = perform_statistical_tests(drift_data)
    
    if not statistical_results:
        st.info("No statistical tests could be performed")
        return
    
    # Display statistical test results
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Distribution Tests")
        
        test_results = []
        for test_name, result in statistical_results.items():
            if 'p_value' in result:
                significance = "Significant" if result['p_value'] < 0.05 else "Not Significant"
                test_results.append({
                    'Test': test_name,
                    'Statistic': f"{result['statistic']:.4f}",
                    'P-value': f"{result['p_value']:.4f}",
                    'Result': significance
                })
        
        if test_results:
            results_df = pd.DataFrame(test_results)
            st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("##### Drift Interpretation")
        
        interpretations = interpret_statistical_results(statistical_results)
        
        for interpretation in interpretations:
            if interpretation['significant']:
                st.warning(f"⚠️ **{interpretation['test']}**: {interpretation['message']}")
            else:
                st.info(f"ℹ️ **{interpretation['test']}**: {interpretation['message']}")

def render_drift_summary(drift_data: pd.DataFrame):
    """Render drift analysis summary"""
    
    st.markdown("#### 📋 Drift Summary")
    
    # Calculate summary statistics
    summary_stats = calculate_drift_summary(drift_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Observations",
            f"{len(drift_data):,}"
        )
    
    with col2:
        if 'timestamp' in drift_data.columns:
            time_span = (drift_data['timestamp'].max() - drift_data['timestamp'].min()).days
            st.metric(
                "Time Span (days)",
                f"{time_span}"
            )
    
    with col3:
        if 'marker_id' in drift_data.columns:
            unique_markers = drift_data['marker_id'].nunique()
            st.metric(
                "Unique Markers",
                f"{unique_markers}"
            )
    
    with col4:
        if 'time_period' in drift_data.columns:
            periods = drift_data['time_period'].nunique()
            st.metric(
                "Time Periods",
                f"{periods}"
            )
    
    # Recommendations
    if summary_stats:
        st.markdown("##### 💡 Recommendations")
        
        recommendations = generate_drift_recommendations(summary_stats, drift_data)
        
        for rec in recommendations:
            st.info(f"• {rec}")

def calculate_drift_indicators(temporal_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Calculate drift indicators from temporal data"""
    
    if temporal_df.empty:
        return pd.DataFrame()
    
    # Calculate rolling statistics for drift detection
    drift_scores = []
    
    for marker in temporal_df['marker_id'].unique():
        marker_data = temporal_df[temporal_df['marker_id'] == marker].sort_values('timestamp')
        
        if len(marker_data) < 3:
            continue
        
        # Calculate rolling mean and variance
        window_size = min(5, len(marker_data))
        marker_data['rolling_mean'] = marker_data['count'].rolling(window=window_size).mean()
        marker_data['rolling_var'] = marker_data['count'].rolling(window=window_size).var()
        
        # Calculate drift score (coefficient of variation)
        marker_data['drift_score'] = (
            marker_data['rolling_var'].fillna(0) / 
            (marker_data['rolling_mean'].fillna(1) + 1)
        )
        
        drift_scores.append(marker_data[['timestamp', 'drift_score']].dropna())
    
    if drift_scores:
        # Combine all drift scores
        combined_drift = pd.concat(drift_scores, ignore_index=True)
        
        # Aggregate drift scores by timestamp
        aggregated_drift = combined_drift.groupby('timestamp')['drift_score'].mean().reset_index()
        
        return aggregated_drift
    
    return pd.DataFrame()

def analyze_pattern_changes(drift_data: pd.DataFrame) -> pd.DataFrame:
    """Analyze pattern changes across time periods"""
    
    if 'time_period' not in drift_data.columns or 'marker_id' not in drift_data.columns:
        return pd.DataFrame()
    
    # Calculate marker distributions per time period
    period_distributions = drift_data.groupby(['time_period', 'marker_id']).size().reset_index()
    period_distributions.columns = ['time_period', 'marker_id', 'count']
    
    # Calculate changes between periods
    pattern_changes = []
    
    periods = sorted(drift_data['time_period'].unique())
    if len(periods) < 2:
        return pd.DataFrame()
    
    for i in range(len(periods) - 1):
        current_period = periods[i]
        next_period = periods[i + 1]
        
        current_dist = period_distributions[period_distributions['time_period'] == current_period]
        next_dist = period_distributions[period_distributions['time_period'] == next_period]
        
        # Merge distributions
        merged = pd.merge(
            current_dist[['marker_id', 'count']],
            next_dist[['marker_id', 'count']],
            on='marker_id',
            how='outer',
            suffixes=('_current', '_next')
        ).fillna(0)
        
        # Calculate changes
        merged['change'] = merged['count_next'] - merged['count_current']
        merged['change_percent'] = (
            merged['change'] / (merged['count_current'] + 1) * 100
        )
        
        merged['from_period'] = current_period
        merged['to_period'] = next_period
        
        pattern_changes.append(merged)
    
    if pattern_changes:
        return pd.concat(pattern_changes, ignore_index=True)
    
    return pd.DataFrame()

def perform_statistical_tests(drift_data: pd.DataFrame) -> Dict[str, Any]:
    """Perform statistical tests for drift detection"""
    
    results = {}
    
    if 'time_period' not in drift_data.columns:
        return results
    
    try:
        # Get data for different time periods
        periods = sorted(drift_data['time_period'].unique())
        
        if len(periods) < 2:
            return results
        
        # Prepare data for statistical tests
        period_data = {}
        for period in periods:
            period_subset = drift_data[drift_data['time_period'] == period]
            if 'marker_id' in period_subset.columns:
                # Count occurrences of each marker
                marker_counts = period_subset['marker_id'].value_counts()
                period_data[period] = marker_counts
        
        if len(period_data) < 2:
            return results
        
        # Chi-square test for distribution changes
        if len(period_data) >= 2:
            period_names = list(period_data.keys())
            
            # Align marker indices
            all_markers = set()
            for counts in period_data.values():
                all_markers.update(counts.index)
            
            # Create contingency table
            contingency = []
            for period in period_names:
                period_counts = []
                for marker in sorted(all_markers):
                    count = period_data[period].get(marker, 0)
                    period_counts.append(count)
                contingency.append(period_counts)
            
            contingency = np.array(contingency)
            
            if contingency.shape[0] >= 2 and contingency.shape[1] >= 2:
                chi2_stat, p_value, _, _ = stats.chi2_contingency(contingency)
                
                results['Chi-square Test'] = {
                    'statistic': chi2_stat,
                    'p_value': p_value,
                    'description': 'Tests for changes in marker distribution across time periods'
                }
        
        # Kolmogorov-Smirnov test for comparing distributions
        if len(periods) == 2:
            early_data = drift_data[drift_data['time_period'] == periods[0]]
            late_data = drift_data[drift_data['time_period'] == periods[-1]]
            
            if 'hour' in drift_data.columns:
                ks_stat, ks_p = stats.ks_2samp(early_data['hour'], late_data['hour'])
                
                results['KS Test (Temporal)'] = {
                    'statistic': ks_stat,
                    'p_value': ks_p,
                    'description': 'Tests for changes in temporal activity patterns'
                }
    
    except Exception as e:
        st.warning(f"Some statistical tests failed: {str(e)}")
    
    return results

def interpret_statistical_results(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Interpret statistical test results"""
    
    interpretations = []
    
    for test_name, result in results.items():
        if 'p_value' not in result:
            continue
        
        significant = result['p_value'] < 0.05
        
        if test_name == 'Chi-square Test':
            if significant:
                message = "Significant changes in marker distribution detected across time periods."
            else:
                message = "No significant changes in marker distribution detected."
        
        elif test_name == 'KS Test (Temporal)':
            if significant:
                message = "Significant changes in temporal activity patterns detected."
            else:
                message = "Temporal activity patterns remain consistent."
        
        else:
            if significant:
                message = "Significant drift detected."
            else:
                message = "No significant drift detected."
        
        interpretations.append({
            'test': test_name,
            'significant': significant,
            'message': message
        })
    
    return interpretations

def calculate_drift_summary(drift_data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate summary statistics for drift analysis"""
    
    summary = {}
    
    if 'timestamp' in drift_data.columns:
        # Time-based statistics
        summary['total_time_span'] = (
            drift_data['timestamp'].max() - drift_data['timestamp'].min()
        ).total_seconds() / 3600  # hours
        
        summary['observation_rate'] = len(drift_data) / (summary['total_time_span'] + 1)
    
    if 'marker_id' in drift_data.columns:
        # Marker diversity
        summary['total_markers'] = drift_data['marker_id'].nunique()
        summary['avg_hits_per_marker'] = len(drift_data) / summary['total_markers']
    
    if 'time_period' in drift_data.columns:
        # Period-based statistics
        period_counts = drift_data['time_period'].value_counts()
        summary['period_balance'] = period_counts.std() / period_counts.mean()
    
    return summary

def generate_drift_recommendations(summary_stats: Dict[str, Any], drift_data: pd.DataFrame) -> List[str]:
    """Generate recommendations based on drift analysis"""
    
    recommendations = []
    
    # Time span recommendations
    if 'total_time_span' in summary_stats:
        if summary_stats['total_time_span'] < 24:  # Less than 1 day
            recommendations.append(
                "Consider collecting data over a longer time period for more reliable drift detection."
            )
        elif summary_stats['total_time_span'] > 720:  # More than 30 days
            recommendations.append(
                "Long data collection period detected. Consider segmenting analysis by weeks or months."
            )
    
    # Observation rate recommendations
    if 'observation_rate' in summary_stats:
        if summary_stats['observation_rate'] < 1:  # Less than 1 observation per hour
            recommendations.append(
                "Low observation rate detected. Consider increasing data collection frequency."
            )
    
    # Marker diversity recommendations
    if 'total_markers' in summary_stats:
        if summary_stats['total_markers'] < 5:
            recommendations.append(
                "Limited marker diversity. Consider expanding marker coverage for comprehensive analysis."
            )
    
    # Period balance recommendations
    if 'period_balance' in summary_stats:
        if summary_stats['period_balance'] > 0.5:
            recommendations.append(
                "Uneven distribution across time periods detected. Consider data rebalancing or weighted analysis."
            )
    
    # Default recommendations
    if not recommendations:
        recommendations.append(
            "Data appears suitable for drift analysis. Monitor trends and consider setting up automated drift alerts."
        )
    
    return recommendations
