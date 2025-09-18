"""
Intuitions-CLU state visualization component for WordThread Marker-Engine
Displays provisional/confirmed/decayed states with multipliers and telemetry
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from utils.performance import performance_monitor


def render_intuitions_panel(analysis_data: Optional[Dict], sqlite_data: Optional[Dict]):
    """Render comprehensive Intuitions-CLU state visualization"""
    
    st.markdown("### 🧠 Intuitions-CLU State Analysis")
    st.markdown("Advanced visualization of intuition states showing provisional, confirmed, and decayed patterns with multipliers and telemetry.")
    
    # Check for intuition data
    intuition_data = extract_intuition_data(analysis_data, sqlite_data)
    
    # Show demo mode banner if using synthetic data
    if getattr(st.session_state, 'using_synthetic_intuitions', False):
        st.warning("🧪 **Demo Mode**: Using synthetic intuition data for demonstration. Upload real data to see actual analysis.")
    
    if not intuition_data or len(intuition_data) == 0:
        render_no_data_message()
        return
    
    # Control panel
    render_intuition_controls(intuition_data)
    
    # Main visualization tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 State Transitions", "📈 Multiplier Analysis", "📡 Telemetry", "🎯 CLU Processing"])
    
    with tab1:
        render_state_transitions(intuition_data)
    
    with tab2:
        render_multiplier_analysis(intuition_data)
    
    with tab3:
        render_telemetry_analysis(intuition_data)
    
    with tab4:
        render_clu_processing(intuition_data)


def extract_intuition_data(analysis_data: Optional[Dict], sqlite_data: Optional[Dict]) -> List[Dict]:
    """Extract intuition data from available sources"""
    
    intuition_records = []
    
    # Extract from AnalysisBundle
    if analysis_data and 'intuitions' in analysis_data:
        intuitions = analysis_data['intuitions']
        for intuition in intuitions:
            record = {
                'id': intuition.get('id', f"intuition_{len(intuition_records)}"),
                'timestamp': intuition.get('timestamp', datetime.now().timestamp()),
                'state': intuition.get('state', 'provisional'),
                'confidence': intuition.get('confidence', 0.5),
                'multiplier': intuition.get('multiplier', 1.0),
                'marker_id': intuition.get('marker_id'),
                'conv_id': intuition.get('conv_id'),
                'telemetry': intuition.get('telemetry', {}),
                'transition_history': intuition.get('transitions', []),
                'source': 'analysis_bundle'
            }
            intuition_records.append(record)
    
    # Extract from SQLite data
    if sqlite_data and 'intuitions' in sqlite_data:
        sqlite_intuitions = sqlite_data['intuitions']
        for intuition in sqlite_intuitions:
            record = {
                'id': intuition.get('intuition_id', f"sqlite_intuition_{len(intuition_records)}"),
                'timestamp': intuition.get('created_at', datetime.now().timestamp()),
                'state': intuition.get('current_state', 'provisional'),
                'confidence': intuition.get('confidence_score', 0.5),
                'multiplier': intuition.get('multiplier_value', 1.0),
                'marker_id': intuition.get('marker_id'),
                'conv_id': intuition.get('conversation_id'),
                'telemetry': parse_telemetry_json(intuition.get('telemetry_data', '{}')),
                'transition_history': parse_transition_history(intuition.get('state_history', '[]')),
                'source': 'sqlite'
            }
            intuition_records.append(record)
    
    # Generate synthetic data if no real data available (for demonstration)
    if not intuition_records:
        # Add flag to indicate synthetic data is being used
        st.session_state.using_synthetic_intuitions = True
        intuition_records = generate_synthetic_intuition_data()
    else:
        st.session_state.using_synthetic_intuitions = False
    
    return intuition_records


def generate_synthetic_intuition_data() -> List[Dict]:
    """Generate synthetic intuition data for demonstration purposes"""
    
    states = ['provisional', 'confirmed', 'decayed']
    synthetic_data = []
    
    base_time = datetime.now().timestamp() - 86400  # 24 hours ago
    
    for i in range(50):
        # Create realistic state progression
        if i < 20:
            state = 'provisional'
            confidence = 0.3 + np.random.random() * 0.4  # 0.3-0.7
            multiplier = 0.8 + np.random.random() * 0.4   # 0.8-1.2
        elif i < 35:
            state = 'confirmed'
            confidence = 0.6 + np.random.random() * 0.3  # 0.6-0.9
            multiplier = 1.0 + np.random.random() * 0.5   # 1.0-1.5
        else:
            state = 'decayed'
            confidence = 0.1 + np.random.random() * 0.3  # 0.1-0.4
            multiplier = 0.5 + np.random.random() * 0.4   # 0.5-0.9
        
        # Create transition history
        transitions = []
        if state == 'confirmed':
            transitions.append({
                'from_state': 'provisional',
                'to_state': 'confirmed',
                'timestamp': base_time + i * 1800 - 900,  # 15 minutes earlier
                'reason': 'confidence_threshold_met'
            })
        elif state == 'decayed':
            transitions.extend([
                {
                    'from_state': 'provisional',
                    'to_state': 'confirmed',
                    'timestamp': base_time + i * 1800 - 1800,
                    'reason': 'confidence_threshold_met'
                },
                {
                    'from_state': 'confirmed',
                    'to_state': 'decayed',
                    'timestamp': base_time + i * 1800 - 600,
                    'reason': 'time_decay'
                }
            ])
        
        record = {
            'id': f"intuition_{i:03d}",
            'timestamp': base_time + i * 1800,  # 30-minute intervals
            'state': state,
            'confidence': confidence,
            'multiplier': multiplier,
            'marker_id': f"marker_{(i % 10) + 1}",
            'conv_id': f"conv_{(i % 5) + 1}",
            'telemetry': {
                'processing_time_ms': 50 + np.random.random() * 200,
                'memory_usage_kb': 1024 + np.random.random() * 2048,
                'cpu_cycles': int(1000 + np.random.random() * 5000),
                'network_calls': int(np.random.random() * 5),
                'cache_hits': int(np.random.random() * 10),
                'cache_misses': int(np.random.random() * 3)
            },
            'transition_history': transitions,
            'source': 'synthetic'
        }
        synthetic_data.append(record)
    
    return synthetic_data


def render_no_data_message():
    """Render message when no intuition data is available"""
    
    st.info("🧠 No intuition data found in the current dataset.")
    
    with st.expander("📚 About Intuitions-CLU Processing"):
        st.markdown("""
        **Intuitions** represent intermediate processing states in the CLU (Cognitive Learning Unit) architecture:
        
        - **Provisional**: Initial intuition formation with low confidence
        - **Confirmed**: Intuition validated through additional evidence or time
        - **Decayed**: Intuition that has lost relevance or confidence over time
        
        **Key Features:**
        - State transition tracking with timestamps
        - Confidence scoring and multiplier effects
        - Telemetry data for performance monitoring
        - Integration with marker processing pipeline
        
        Upload data containing intuition records to see detailed analysis.
        """)


def render_intuition_controls(intuition_data: List[Dict]):
    """Render control panel for filtering and analysis options"""
    
    st.markdown("#### 🎛️ Analysis Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # State filter
        all_states = list(set(item['state'] for item in intuition_data))
        selected_states = st.multiselect(
            "Filter by State",
            options=all_states,
            default=all_states,
            key="intuition_state_filter"
        )
    
    with col2:
        # Confidence threshold
        confidence_threshold = st.slider(
            "Min Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            key="confidence_threshold"
        )
    
    with col3:
        # Time range filter
        timestamps = [item['timestamp'] for item in intuition_data]
        time_range = None
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            
            time_range = st.slider(
                "Time Range (hours ago)",
                min_value=0,
                max_value=int((max_time - min_time) / 3600) + 1,
                value=(0, int((max_time - min_time) / 3600) + 1),
                key="time_range_filter"
            )
    
    with col4:
        # Marker filter
        all_markers = list(set(item['marker_id'] for item in intuition_data if item['marker_id']))
        selected_markers = st.multiselect(
            "Filter by Marker",
            options=all_markers,
            default=all_markers[:5] if len(all_markers) > 5 else all_markers,
            key="marker_filter"
        )
    
    # Store filters in session state
    st.session_state.intuition_filters = {
        'states': selected_states,
        'confidence_threshold': confidence_threshold,
        'time_range': time_range,
        'markers': selected_markers
    }


def render_state_transitions(intuition_data: List[Dict]):
    """Render state transition visualization"""
    
    st.markdown("#### 🔄 Intuition State Transitions")
    
    # Apply filters
    filtered_data = apply_intuition_filters(intuition_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    # State distribution
    col1, col2 = st.columns(2)
    
    with col1:
        render_state_distribution(filtered_data)
    
    with col2:
        render_confidence_by_state(filtered_data)
    
    # State transition timeline
    render_state_timeline(filtered_data)
    
    # Transition matrix
    render_transition_matrix(filtered_data)


def render_state_distribution(data: List[Dict]):
    """Render state distribution pie chart"""
    
    st.markdown("##### 📊 State Distribution")
    
    state_counts = {}
    for item in data:
        state = item['state']
        state_counts[state] = state_counts.get(state, 0) + 1
    
    if state_counts:
        fig = go.Figure(data=[go.Pie(
            labels=list(state_counts.keys()),
            values=list(state_counts.values()),
            hole=0.4,
            marker_colors=['#FF8C00', '#FFD700', '#FF6347']
        )])
        
        fig.update_layout(
            title="Current State Distribution",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No state data available")


def render_confidence_by_state(data: List[Dict]):
    """Render confidence distribution by state"""
    
    st.markdown("##### 📈 Confidence by State")
    
    df = pd.DataFrame(data)
    
    if not df.empty and 'confidence' in df.columns:
        fig = go.Figure()
        
        for state in df['state'].unique():
            state_data = df[df['state'] == state]
            
            fig.add_trace(go.Box(
                y=state_data['confidence'],
                name=state,
                boxpoints='outliers',
                marker_color=get_state_color(state)
            ))
        
        fig.update_layout(
            title="Confidence Distribution by State",
            yaxis_title="Confidence Score",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No confidence data available")


def render_state_timeline(data: List[Dict]):
    """Render state transition timeline"""
    
    st.markdown("##### ⏱️ State Timeline")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if not df.empty:
        fig = go.Figure()
        
        # Add traces for each state
        for state in df['state'].unique():
            state_data = df[df['state'] == state]
            
            fig.add_trace(go.Scatter(
                x=state_data['datetime'],
                y=state_data['confidence'],
                mode='markers+lines',
                name=state,
                marker=dict(
                    size=8,
                    color=get_state_color(state),
                    symbol=get_state_symbol(state)
                ),
                line=dict(color=get_state_color(state), width=2),
                hovertemplate=f"<b>{state}</b><br>" +
                              "Time: %{x}<br>" +
                              "Confidence: %{y:.2f}<br>" +
                              "<extra></extra>"
            ))
        
        fig.update_layout(
            title="Intuition State Timeline",
            xaxis_title="Time",
            yaxis_title="Confidence Score",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400,
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available")


def render_transition_matrix(data: List[Dict]):
    """Render state transition matrix"""
    
    st.markdown("##### 🔄 Transition Matrix")
    
    # Extract transitions from history
    transitions = []
    for item in data:
        if item.get('transition_history'):
            for transition in item['transition_history']:
                transitions.append({
                    'from': transition.get('from_state'),
                    'to': transition.get('to_state'),
                    'timestamp': transition.get('timestamp')
                })
    
    if transitions:
        df = pd.DataFrame(transitions)
        
        # Create transition matrix
        transition_matrix = pd.crosstab(df['from'], df['to'], margins=True)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=transition_matrix.values,
            x=transition_matrix.columns,
            y=transition_matrix.index,
            colorscale='Viridis',
            text=transition_matrix.values,
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="State Transition Matrix",
            xaxis_title="To State",
            yaxis_title="From State",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transition data available")


def render_multiplier_analysis(intuition_data: List[Dict]):
    """Render multiplier analysis visualization"""
    
    st.markdown("#### 📈 Multiplier Analysis")
    
    filtered_data = apply_intuition_filters(intuition_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_multiplier_distribution(filtered_data)
    
    with col2:
        render_multiplier_vs_confidence(filtered_data)
    
    # Multiplier evolution over time
    render_multiplier_timeline(filtered_data)
    
    # Multiplier statistics
    render_multiplier_statistics(filtered_data)


def render_multiplier_distribution(data: List[Dict]):
    """Render multiplier distribution histogram"""
    
    st.markdown("##### 📊 Multiplier Distribution")
    
    multipliers = [item['multiplier'] for item in data if item.get('multiplier')]
    
    if multipliers:
        fig = go.Figure(data=[go.Histogram(
            x=multipliers,
            nbinsx=20,
            marker_color='#FFD700',
            opacity=0.7
        )])
        
        fig.update_layout(
            title="Multiplier Value Distribution",
            xaxis_title="Multiplier Value",
            yaxis_title="Frequency",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No multiplier data available")


def render_multiplier_vs_confidence(data: List[Dict]):
    """Render multiplier vs confidence scatter plot"""
    
    st.markdown("##### 🎯 Multiplier vs Confidence")
    
    df = pd.DataFrame(data)
    
    if not df.empty and 'multiplier' in df.columns and 'confidence' in df.columns:
        fig = go.Figure()
        
        for state in df['state'].unique():
            state_data = df[df['state'] == state]
            
            fig.add_trace(go.Scatter(
                x=state_data['confidence'],
                y=state_data['multiplier'],
                mode='markers',
                name=state,
                marker=dict(
                    size=8,
                    color=get_state_color(state),
                    opacity=0.7
                ),
                hovertemplate=f"<b>{state}</b><br>" +
                              "Confidence: %{x:.2f}<br>" +
                              "Multiplier: %{y:.2f}<br>" +
                              "<extra></extra>"
            ))
        
        fig.update_layout(
            title="Multiplier vs Confidence Correlation",
            xaxis_title="Confidence Score",
            yaxis_title="Multiplier Value",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No correlation data available")


def render_multiplier_timeline(data: List[Dict]):
    """Render multiplier evolution timeline"""
    
    st.markdown("##### ⏱️ Multiplier Evolution")
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    if not df.empty and 'multiplier' in df.columns:
        fig = go.Figure()
        
        # Rolling average
        df['multiplier_ma'] = df['multiplier'].rolling(window=5, center=True, min_periods=1).mean()
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['multiplier'],
            mode='markers',
            name='Raw Multiplier',
            marker=dict(size=4, color='#FF8C00', opacity=0.6),
            hovertemplate="Time: %{x}<br>Multiplier: %{y:.2f}<extra></extra>"
        ))
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['multiplier_ma'],
            mode='lines',
            name='Moving Average',
            line=dict(color='#FFD700', width=3),
            hovertemplate="Time: %{x}<br>Avg Multiplier: %{y:.2f}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Multiplier Evolution Over Time",
            xaxis_title="Time",
            yaxis_title="Multiplier Value",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available")


def render_multiplier_statistics(data: List[Dict]):
    """Render multiplier statistics summary"""
    
    st.markdown("##### 📊 Multiplier Statistics")
    
    multipliers = [item['multiplier'] for item in data if item.get('multiplier')]
    
    if multipliers:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean Multiplier", f"{np.mean(multipliers):.3f}")
        
        with col2:
            st.metric("Median Multiplier", f"{np.median(multipliers):.3f}")
        
        with col3:
            st.metric("Max Multiplier", f"{np.max(multipliers):.3f}")
        
        with col4:
            st.metric("Std Deviation", f"{np.std(multipliers):.3f}")
        
        # Multiplier ranges by state
        df = pd.DataFrame(data)
        if 'state' in df.columns:
            state_stats = df.groupby('state')['multiplier'].agg(['mean', 'std', 'min', 'max'])
            st.markdown("**Multiplier Statistics by State:**")
            st.dataframe(state_stats, use_container_width=True)
    else:
        st.info("No multiplier statistics available")


def render_telemetry_analysis(intuition_data: List[Dict]):
    """Render telemetry analysis"""
    
    st.markdown("#### 📡 Telemetry Analysis")
    
    filtered_data = apply_intuition_filters(intuition_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    # Extract telemetry data
    telemetry_df = extract_telemetry_dataframe(filtered_data)
    
    if telemetry_df.empty:
        st.info("No telemetry data available")
        return
    
    # Performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        render_performance_metrics(telemetry_df)
    
    with col2:
        render_resource_usage(telemetry_df)
    
    # Detailed telemetry analysis
    render_telemetry_correlations(telemetry_df)


def render_clu_processing(intuition_data: List[Dict]):
    """Render CLU processing analysis"""
    
    st.markdown("#### 🎯 CLU Processing Analysis")
    
    filtered_data = apply_intuition_filters(intuition_data)
    
    if not filtered_data:
        st.warning("No data matches the current filters.")
        return
    
    # Processing pipeline visualization
    render_processing_pipeline(filtered_data)
    
    # CLU performance metrics
    render_clu_performance(filtered_data)


def apply_intuition_filters(data: List[Dict]) -> List[Dict]:
    """Apply current filters to intuition data"""
    
    if 'intuition_filters' not in st.session_state:
        return data
    
    filters = st.session_state.intuition_filters
    filtered_data = data
    
    # State filter
    if filters.get('states'):
        filtered_data = [item for item in filtered_data if item['state'] in filters['states']]
    
    # Confidence filter
    if filters.get('confidence_threshold') is not None:
        filtered_data = [item for item in filtered_data if item['confidence'] >= filters['confidence_threshold']]
    
    # Marker filter
    if filters.get('markers'):
        filtered_data = [item for item in filtered_data if item['marker_id'] in filters['markers']]
    
    # Time range filter (simplified for now)
    # TODO: Implement proper time range filtering
    
    return filtered_data


def extract_telemetry_dataframe(data: List[Dict]) -> pd.DataFrame:
    """Extract telemetry data into a DataFrame"""
    
    telemetry_records = []
    
    for item in data:
        if item.get('telemetry'):
            record = {
                'id': item['id'],
                'state': item['state'],
                'timestamp': item['timestamp'],
                **item['telemetry']  # Flatten telemetry data
            }
            telemetry_records.append(record)
    
    return pd.DataFrame(telemetry_records)


def render_performance_metrics(telemetry_df: pd.DataFrame):
    """Render performance metrics from telemetry"""
    
    st.markdown("##### ⚡ Performance Metrics")
    
    if 'processing_time_ms' in telemetry_df.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=telemetry_df['processing_time_ms'],
            nbinsx=20,
            marker_color='#FF8C00',
            name='Processing Time'
        ))
        
        fig.update_layout(
            title="Processing Time Distribution",
            xaxis_title="Processing Time (ms)",
            yaxis_title="Frequency",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No processing time data available")


def render_resource_usage(telemetry_df: pd.DataFrame):
    """Render resource usage metrics"""
    
    st.markdown("##### 💾 Resource Usage")
    
    if 'memory_usage_kb' in telemetry_df.columns:
        fig = go.Figure()
        
        # Memory usage over time
        fig.add_trace(go.Scatter(
            x=telemetry_df.index,
            y=telemetry_df['memory_usage_kb'],
            mode='lines+markers',
            name='Memory Usage',
            line=dict(color='#FFD700', width=2)
        ))
        
        fig.update_layout(
            title="Memory Usage Pattern",
            xaxis_title="Sample Index",
            yaxis_title="Memory Usage (KB)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No memory usage data available")


def render_telemetry_correlations(telemetry_df: pd.DataFrame):
    """Render telemetry correlation analysis"""
    
    st.markdown("##### 🔗 Telemetry Correlations")
    
    numeric_columns = telemetry_df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_columns) > 1:
        correlation_matrix = telemetry_df[numeric_columns].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Telemetry Metrics Correlation",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient numeric data for correlation analysis")


def render_processing_pipeline(data: List[Dict]):
    """Render CLU processing pipeline visualization"""
    
    st.markdown("##### 🔄 Processing Pipeline")
    
    # Create pipeline flow diagram
    pipeline_stages = ['ATO', 'SEM', 'CLU', 'MEMA']
    stage_counts = {stage: 0 for stage in pipeline_stages}
    
    # Count stages (simplified - would need actual pipeline data)
    for item in data:
        # Simulate pipeline stage assignment based on state
        if item['state'] == 'provisional':
            stage_counts['ATO'] += 1
        elif item['state'] == 'confirmed':
            stage_counts['CLU'] += 1
        elif item['state'] == 'decayed':
            stage_counts['MEMA'] += 1
    
    # Create sankey diagram for pipeline flow
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=pipeline_stages,
            color=['#FF8C00', '#FFD700', '#FF6347', '#32CD32']
        ),
        link=dict(
            source=[0, 1, 2],  # ATO->SEM, SEM->CLU, CLU->MEMA
            target=[1, 2, 3],
            value=[stage_counts['ATO'], stage_counts['SEM'], stage_counts['CLU']]
        )
    )])
    
    fig.update_layout(
        title="ATO → SEM → CLU → MEMA Pipeline Flow",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_clu_performance(data: List[Dict]):
    """Render CLU-specific performance metrics"""
    
    st.markdown("##### 🎯 CLU Performance")
    
    # Calculate CLU metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        confirmed_count = len([item for item in data if item['state'] == 'confirmed'])
        st.metric("Confirmed Intuitions", confirmed_count)
    
    with col2:
        avg_confidence = np.mean([item['confidence'] for item in data if item['state'] == 'confirmed'])
        st.metric("Avg Confirmed Confidence", f"{avg_confidence:.3f}")
    
    with col3:
        avg_multiplier = np.mean([item['multiplier'] for item in data if item['state'] == 'confirmed'])
        st.metric("Avg Confirmed Multiplier", f"{avg_multiplier:.3f}")


def get_state_color(state: str) -> str:
    """Get color for a given state"""
    colors = {
        'provisional': '#FF8C00',  # Orange
        'confirmed': '#FFD700',   # Gold
        'decayed': '#FF6347'      # Tomato
    }
    return colors.get(state, '#888888')


def get_state_symbol(state: str) -> str:
    """Get symbol for a given state"""
    symbols = {
        'provisional': 'circle',
        'confirmed': 'diamond',
        'decayed': 'x'
    }
    return symbols.get(state, 'circle')


def parse_telemetry_json(telemetry_str: str) -> Dict:
    """Parse telemetry JSON string safely"""
    try:
        import json
        return json.loads(telemetry_str)
    except:
        return {}


def parse_transition_history(history_str: str) -> List[Dict]:
    """Parse transition history JSON string safely"""
    try:
        import json
        return json.loads(history_str)
    except:
        return []