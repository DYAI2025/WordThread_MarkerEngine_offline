"""
Performance monitoring dashboard for WordThread Marker-Engine
Displays FPS, paint time metrics, and data processing performance
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import psutil
import numpy as np
from typing import Dict, Any, List, Optional
from utils.performance import performance_monitor
from datetime import datetime, timedelta


def render_performance_dashboard():
    """Render comprehensive performance monitoring dashboard"""
    
    st.markdown("### ⚡ Performance Monitoring Dashboard")
    st.markdown("Real-time monitoring of application performance, data processing, and system resources.")
    
    # Create tabs for different performance aspects
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Processing", "🖥️ System Resources", "📈 Chart Performance", "🔍 Detailed Metrics"])
    
    with tab1:
        render_data_processing_metrics()
    
    with tab2:
        render_system_metrics()
    
    with tab3:
        render_chart_performance_metrics()
    
    with tab4:
        render_detailed_metrics()


def render_data_processing_metrics():
    """Render data processing performance metrics"""
    
    st.markdown("#### 📊 Data Processing Performance")
    
    # Get performance summary
    perf_summary = performance_monitor.get_performance_summary()
    
    if perf_summary.get('status') == 'no_data':
        st.info("📈 No performance data available yet. Process some data to see metrics.")
        return
    
    # Performance score and key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = perf_summary.get('performance_score', 0)
        score_color = get_score_color(score)
        st.metric(
            "Performance Score",
            f"{score:.0f}/100",
            help="Overall performance score based on processing times"
        )
        
        # Add visual indicator
        if score >= 80:
            st.success("🟢 Excellent Performance")
        elif score >= 60:
            st.warning("🟡 Good Performance")
        else:
            st.error("🔴 Performance Issues Detected")
    
    with col2:
        avg_time = perf_summary.get('avg_processing_time_ms', 0)
        st.metric(
            "Avg Processing Time",
            f"{avg_time:.1f}ms",
            help="Average time for data processing operations"
        )
    
    with col3:
        max_data_size = perf_summary.get('max_data_size', 0)
        st.metric(
            "Max Data Size",
            f"{max_data_size:,} points",
            help="Largest dataset processed"
        )
    
    with col4:
        total_ops = perf_summary.get('total_operations', 0)
        st.metric(
            "Total Operations",
            f"{total_ops:,}",
            help="Number of processing operations completed"
        )
    
    # Performance trend chart
    if performance_monitor.metrics['processing_times']:
        render_performance_trend_chart()
    
    # Downsampling efficiency
    render_downsampling_metrics()


def render_system_metrics():
    """Render system resource metrics"""
    
    st.markdown("#### 🖥️ System Resource Usage")
    
    # Get current system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "CPU Usage",
            f"{cpu_percent:.1f}%",
            help="Current CPU utilization"
        )
        
        # CPU progress bar
        cpu_color = "green" if cpu_percent < 70 else "orange" if cpu_percent < 90 else "red"
        st.progress(cpu_percent / 100)
    
    with col2:
        memory_percent = memory.percent
        st.metric(
            "Memory Usage",
            f"{memory_percent:.1f}%",
            help=f"RAM usage: {memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB"
        )
        
        # Memory progress bar
        memory_color = "green" if memory_percent < 70 else "orange" if memory_percent < 90 else "red"
        st.progress(memory_percent / 100)
    
    with col3:
        disk_percent = disk.percent
        st.metric(
            "Disk Usage",
            f"{disk_percent:.1f}%",
            help=f"Disk usage: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB"
        )
        
        # Disk progress bar
        st.progress(disk_percent / 100)
    
    with col4:
        # Estimate FPS based on processing performance
        fps = estimate_fps()
        st.metric(
            "Estimated FPS",
            f"{fps:.1f}",
            help="Estimated frames per second for real-time updates"
        )
    
    # Real-time system monitoring chart
    render_system_monitoring_chart()


def render_chart_performance_metrics():
    """Render chart-specific performance metrics"""
    
    st.markdown("#### 📈 Chart Rendering Performance")
    
    # Chart performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### ⏱️ Rendering Times")
        
        # Get chart rendering times from performance monitor
        chart_metrics = get_chart_performance_metrics()
        
        if chart_metrics:
            for chart_type, metrics in chart_metrics.items():
                st.write(f"**{chart_type}**: {metrics['avg_time']:.1f}ms avg")
                st.progress(min(metrics['avg_time'] / 1000, 1.0))  # Cap at 1000ms for progress bar
        else:
            st.info("Render some charts to see performance metrics")
    
    with col2:
        st.markdown("##### 📊 Data Points vs Performance")
        
        # Show relationship between data size and performance
        render_data_size_performance_chart()
    
    # Performance recommendations
    render_performance_recommendations()


def render_detailed_metrics():
    """Render detailed performance metrics and logs"""
    
    st.markdown("#### 🔍 Detailed Performance Metrics")
    
    # Detailed performance data table
    if performance_monitor.metrics['processing_times']:
        st.markdown("##### Recent Operations")
        
        # Create DataFrame from recent operations
        recent_ops = performance_monitor.metrics['processing_times'][-20:]  # Last 20 operations
        
        if recent_ops:
            ops_df = pd.DataFrame(recent_ops)
            ops_df['timestamp'] = pd.to_datetime(ops_df['timestamp'], unit='s')
            ops_df = ops_df.sort_values('timestamp', ascending=False)
            
            st.dataframe(
                ops_df[['operation', 'duration_ms', 'timestamp']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'operation': st.column_config.TextColumn('Operation'),
                    'duration_ms': st.column_config.NumberColumn('Duration (ms)', format="%.1f"),
                    'timestamp': st.column_config.DatetimeColumn('Timestamp')
                }
            )
    
    # Performance analysis
    render_performance_analysis()
    
    # Debug information
    with st.expander("🛠️ Debug Information"):
        st.markdown("**Performance Monitor State:**")
        st.json({
            'total_operations': len(performance_monitor.metrics['processing_times']),
            'data_sizes_tracked': len(performance_monitor.metrics['data_sizes']),
            'downsample_operations': len(performance_monitor.metrics['downsample_ratios']),
            'memory_usage_tracked': len(performance_monitor.metrics['memory_usage'])
        })


def render_performance_trend_chart():
    """Render performance trend over time"""
    
    st.markdown("##### 📈 Performance Trends")
    
    # Get processing times data
    processing_data = performance_monitor.metrics['processing_times']
    
    if len(processing_data) < 2:
        st.info("Need more data points to show trends")
        return
    
    # Create DataFrame
    df = pd.DataFrame(processing_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('timestamp')
    
    # Create trend chart
    fig = go.Figure()
    
    # Group by operation type
    for operation in df['operation'].unique():
        op_data = df[df['operation'] == operation]
        
        fig.add_trace(go.Scatter(
            x=op_data['timestamp'],
            y=op_data['duration_ms'],
            mode='lines+markers',
            name=operation,
            line=dict(width=2),
            opacity=0.8
        ))
    
    fig.update_layout(
        title="Processing Time Trends",
        xaxis_title="Time",
        yaxis_title="Duration (ms)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_downsampling_metrics():
    """Render downsampling efficiency metrics"""
    
    st.markdown("##### 🎯 Downsampling Efficiency")
    
    downsample_data = performance_monitor.metrics['downsample_ratios']
    
    if not downsample_data:
        st.info("No downsampling operations recorded yet")
        return
    
    # Calculate downsampling statistics
    ratios = [d['ratio'] for d in downsample_data]
    avg_ratio = np.mean(ratios)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Avg Compression Ratio",
            f"{avg_ratio:.2f}",
            help="Average ratio of downsampled to original data"
        )
    
    with col2:
        data_saved = (1 - avg_ratio) * 100
        st.metric(
            "Data Reduction",
            f"{data_saved:.1f}%",
            help="Percentage of data points reduced through downsampling"
        )
    
    with col3:
        st.metric(
            "Downsample Operations",
            f"{len(downsample_data):,}",
            help="Total number of downsampling operations performed"
        )


def render_system_monitoring_chart():
    """Render real-time system monitoring chart"""
    
    # This would typically connect to a real-time monitoring system
    # For now, show current values
    
    current_time = datetime.now()
    times = [current_time - timedelta(minutes=i) for i in range(10, 0, -1)]
    
    # Simulate historical data (in a real implementation, this would come from a monitoring system)
    cpu_data = [psutil.cpu_percent() + np.random.normal(0, 5) for _ in times]
    memory_data = [psutil.virtual_memory().percent + np.random.normal(0, 3) for _ in times]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['CPU Usage (%)', 'Memory Usage (%)'],
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(x=times, y=cpu_data, name='CPU', line=dict(color='#FF8C00')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=times, y=memory_data, name='Memory', line=dict(color='#FFD700')),
        row=2, col=1
    )
    
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_data_size_performance_chart():
    """Render chart showing relationship between data size and performance"""
    
    processing_times = performance_monitor.metrics['processing_times']
    data_sizes = performance_monitor.metrics['data_sizes']
    
    if not processing_times or not data_sizes:
        st.info("Process data to see performance vs. size analysis")
        return
    
    # Match processing times with data sizes by timestamp
    matched_data = []
    for proc_time in processing_times:
        # Find closest data size entry by timestamp
        closest_size = min(data_sizes, key=lambda x: abs(x['timestamp'] - proc_time['timestamp']))
        matched_data.append({
            'size': closest_size['size'],
            'duration': proc_time['duration_ms'],
            'operation': proc_time['operation']
        })
    
    if matched_data:
        df = pd.DataFrame(matched_data)
        
        fig = go.Figure()
        
        # Group by operation type
        for operation in df['operation'].unique():
            op_data = df[df['operation'] == operation]
            
            fig.add_trace(go.Scatter(
                x=op_data['size'],
                y=op_data['duration'],
                mode='markers',
                name=operation,
                marker=dict(size=8, opacity=0.7)
            ))
        
        fig.update_layout(
            title="Data Size vs Performance",
            xaxis_title="Data Size (points)",
            yaxis_title="Processing Time (ms)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_performance_recommendations():
    """Render performance optimization recommendations"""
    
    st.markdown("##### 💡 Performance Recommendations")
    
    perf_summary = performance_monitor.get_performance_summary()
    recommendations = []
    
    if perf_summary.get('status') != 'no_data':
        avg_time = perf_summary.get('avg_processing_time_ms', 0)
        max_time = perf_summary.get('max_processing_time_ms', 0)
        max_size = perf_summary.get('max_data_size', 0)
        
        if avg_time > 500:
            recommendations.append("⚠️ Consider enabling more aggressive downsampling for better performance")
        
        if max_time > 2000:
            recommendations.append("🔍 Some operations are taking >2 seconds - investigate data complexity")
        
        if max_size > 50000:
            recommendations.append("📊 Very large datasets detected - ensure LTTB downsampling is active")
        
        # System-based recommendations
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            recommendations.append("💾 High memory usage detected - consider reducing data retention")
        
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > 80:
            recommendations.append("🖥️ High CPU usage - consider optimizing processing algorithms")
    
    if not recommendations:
        recommendations.append("✅ Performance is optimal - no recommendations at this time")
    
    for rec in recommendations:
        st.info(rec)


def render_performance_analysis():
    """Render detailed performance analysis"""
    
    st.markdown("##### 📊 Performance Analysis")
    
    perf_summary = performance_monitor.get_performance_summary()
    
    if perf_summary.get('status') == 'no_data':
        st.info("No performance data available for analysis")
        return
    
    # Performance breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Processing Time Distribution:**")
        
        processing_times = [p['duration_ms'] for p in performance_monitor.metrics['processing_times']]
        if processing_times:
            percentiles = np.percentile(processing_times, [25, 50, 75, 90, 95])
            
            st.write(f"25th percentile: {percentiles[0]:.1f}ms")
            st.write(f"50th percentile: {percentiles[1]:.1f}ms")
            st.write(f"75th percentile: {percentiles[2]:.1f}ms")
            st.write(f"90th percentile: {percentiles[3]:.1f}ms")
            st.write(f"95th percentile: {percentiles[4]:.1f}ms")
    
    with col2:
        st.markdown("**Performance Insights:**")
        
        if processing_times:
            variability = np.std(processing_times) / np.mean(processing_times) if np.mean(processing_times) > 0 else 0
            
            if variability < 0.3:
                st.success("🟢 Consistent performance")
            elif variability < 0.7:
                st.warning("🟡 Moderate performance variation")
            else:
                st.error("🔴 High performance variability")
            
            st.write(f"Coefficient of variation: {variability:.2f}")


def get_chart_performance_metrics() -> Dict[str, Dict[str, float]]:
    """Get performance metrics specific to chart rendering"""
    
    chart_metrics = {}
    
    # Group processing times by operation type
    for metric in performance_monitor.metrics['processing_times']:
        operation = metric['operation']
        duration = metric['duration_ms']
        
        if 'chart' in operation.lower() or 'render' in operation.lower():
            if operation not in chart_metrics:
                chart_metrics[operation] = {'times': [], 'avg_time': 0}
            
            chart_metrics[operation]['times'].append(duration)
    
    # Calculate averages
    for operation in chart_metrics:
        times = chart_metrics[operation]['times']
        chart_metrics[operation]['avg_time'] = np.mean(times) if times else 0
    
    return chart_metrics


def get_score_color(score: float) -> str:
    """Get color based on performance score"""
    if score >= 80:
        return "green"
    elif score >= 60:
        return "orange"
    else:
        return "red"


def estimate_fps() -> float:
    """Estimate FPS based on recent performance metrics"""
    
    processing_times = performance_monitor.metrics['processing_times']
    
    if not processing_times:
        return 0.0
    
    # Get recent processing times
    recent_times = [p['duration_ms'] for p in processing_times[-10:]]
    
    if not recent_times:
        return 0.0
    
    # Estimate FPS as 1000 / average_processing_time (assuming 1 frame per processing cycle)
    avg_time = np.mean(recent_times)
    
    if avg_time <= 0:
        return 0.0
    
    fps = 1000.0 / avg_time
    
    # Cap at reasonable values
    return min(fps, 60.0)