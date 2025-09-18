import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
import plotly.express as px
import plotly.graph_objects as go

def render_markers_table(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]):
    """Render interactive markers table with filtering and selection"""
    
    st.markdown("### 🎯 Marker Analysis")
    
    if not analysis_data and not sqlite_data:
        st.info("📋 No marker data available. Please upload data files.")
        return
    
    # Prepare marker data
    markers_df = prepare_markers_data(analysis_data, sqlite_data)
    
    if markers_df.empty:
        st.warning("⚠️ No marker data found in uploaded files")
        return
    
    # Render filtering controls
    filtered_df = render_marker_filters(markers_df)
    
    # Render main markers table
    render_main_markers_table(filtered_df)
    
    # Render marker details and statistics
    render_marker_statistics(filtered_df)
    
    # Render marker architecture visualization
    render_marker_architecture(filtered_df)

def prepare_markers_data(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare and combine marker data from different sources"""
    
    data_frames = []
    
    # Process analysis bundle data
    if analysis_data and 'hits' in analysis_data:
        hits_df = pd.DataFrame(analysis_data['hits'])
        
        if not hits_df.empty:
            # Convert timestamp
            if 'ts' in hits_df.columns:
                hits_df['timestamp'] = pd.to_datetime(hits_df['ts'], unit='s')
            
            # Add source identifier
            hits_df['source'] = 'analysis_bundle'
            data_frames.append(hits_df)
    
    # Process SQLite data
    if sqlite_data and 'tables' in sqlite_data and 'hits' in sqlite_data['tables']:
        sqlite_hits = pd.DataFrame(sqlite_data['tables']['hits'])
        
        if not sqlite_hits.empty:
            # Standardize columns
            if 'ts' in sqlite_hits.columns:
                sqlite_hits['timestamp'] = pd.to_datetime(sqlite_hits['ts'], unit='s')
            
            sqlite_hits['source'] = 'sqlite'
            data_frames.append(sqlite_hits)
    
    # Combine and process data
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        
        # Add marker categorization
        combined_df = add_marker_categories(combined_df)
        
        # Calculate marker statistics
        combined_df = calculate_marker_stats(combined_df)
        
        return combined_df
    
    return pd.DataFrame()

def add_marker_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Add marker category and type information"""
    
    def categorize_marker(marker_id: str) -> str:
        """Categorize marker based on prefix"""
        if marker_id.startswith('ATO_'):
            return 'ATO'
        elif marker_id.startswith('SEM_'):
            return 'SEM'
        elif marker_id.startswith('CLU_'):
            return 'CLU'
        elif marker_id.startswith('MEMA_'):
            return 'MEMA'
        else:
            return 'UNKNOWN'
    
    def get_marker_type(marker_id: str) -> str:
        """Extract marker type from ID"""
        if '_' in marker_id:
            parts = marker_id.split('_')
            if len(parts) > 1:
                return '_'.join(parts[1:])
        return marker_id
    
    if 'marker_id' in df.columns:
        df['marker_category'] = df['marker_id'].apply(categorize_marker)
        df['marker_type'] = df['marker_id'].apply(get_marker_type)
    
    return df

def calculate_marker_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate statistics for each marker"""
    
    if 'marker_id' not in df.columns:
        return df
    
    # Group by marker_id and calculate stats
    marker_stats = df.groupby('marker_id').agg({
        'id': 'count',  # Hit count
        'ts': ['min', 'max'] if 'ts' in df.columns else None,
        'conv': 'nunique' if 'conv' in df.columns else None
    }).round(2)
    
    # Flatten column names
    marker_stats.columns = ['_'.join(col).strip() for col in marker_stats.columns.values]
    
    # Rename columns for clarity
    column_mapping = {
        'id_count': 'hit_count',
        'ts_min': 'first_seen',
        'ts_max': 'last_seen',
        'conv_nunique': 'conversation_count'
    }
    
    marker_stats = marker_stats.rename(columns=column_mapping)
    
    # Calculate additional metrics
    if 'first_seen' in marker_stats.columns and 'last_seen' in marker_stats.columns:
        marker_stats['activity_duration'] = marker_stats['last_seen'] - marker_stats['first_seen']
        marker_stats['activity_rate'] = marker_stats['hit_count'] / (marker_stats['activity_duration'] + 1)
    
    return marker_stats.reset_index()

def render_marker_filters(markers_df: pd.DataFrame) -> pd.DataFrame:
    """Render filtering controls for markers table"""
    
    st.markdown("#### 🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Category filter
        if 'marker_category' in markers_df.columns:
            categories = ['All'] + sorted(markers_df['marker_category'].unique().tolist())
            selected_category = st.selectbox(
                "Category",
                categories,
                help="Filter by marker category (ATO/SEM/CLU/MEMA)"
            )
        else:
            selected_category = 'All'
    
    with col2:
        # Hit count filter
        if 'hit_count' in markers_df.columns:
            min_hits = int(markers_df['hit_count'].min())
            max_hits = int(markers_df['hit_count'].max())
            hit_threshold = st.slider(
                "Min Hits",
                min_value=min_hits,
                max_value=max_hits,
                value=min_hits,
                help="Filter markers by minimum hit count"
            )
        else:
            hit_threshold = 0
    
    with col3:
        # Search filter
        search_term = st.text_input(
            "Search Markers",
            placeholder="Enter marker ID or type...",
            help="Search for specific markers"
        )
    
    with col4:
        # Sort options
        sort_options = {
            'Hit Count (Desc)': ('hit_count', False),
            'Hit Count (Asc)': ('hit_count', True),
            'Marker ID': ('marker_id', True),
            'Category': ('marker_category', True)
        }
        
        sort_selection = st.selectbox(
            "Sort By",
            list(sort_options.keys()),
            help="Sort markers table"
        )
    
    # Apply filters
    filtered_df = markers_df.copy()
    
    # Category filter
    if selected_category != 'All' and 'marker_category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['marker_category'] == selected_category]
    
    # Hit count filter
    if 'hit_count' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['hit_count'] >= hit_threshold]
    
    # Search filter
    if search_term and 'marker_id' in filtered_df.columns:
        mask = filtered_df['marker_id'].str.contains(search_term, case=False, na=False)
        if 'marker_type' in filtered_df.columns:
            mask |= filtered_df['marker_type'].str.contains(search_term, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    # Apply sorting
    if sort_selection in sort_options:
        sort_col, ascending = sort_options[sort_selection]
        if sort_col in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_col, ascending=ascending)
    
    return filtered_df

def render_main_markers_table(markers_df: pd.DataFrame):
    """Render the main markers data table"""
    
    st.markdown("#### 📋 Markers Table")
    
    if markers_df.empty:
        st.info("No markers match the current filters")
        return
    
    # Prepare display columns
    display_columns = ['marker_id']
    
    if 'marker_category' in markers_df.columns:
        display_columns.append('marker_category')
    
    if 'marker_type' in markers_df.columns:
        display_columns.append('marker_type')
    
    if 'hit_count' in markers_df.columns:
        display_columns.append('hit_count')
    
    if 'conversation_count' in markers_df.columns:
        display_columns.append('conversation_count')
    
    if 'activity_rate' in markers_df.columns:
        display_columns.append('activity_rate')
    
    # Display the table with selection
    selected_rows = st.data_editor(
        markers_df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            'marker_id': st.column_config.TextColumn('Marker ID', width='medium'),
            'marker_category': st.column_config.SelectboxColumn(
                'Category',
                options=['ATO', 'SEM', 'CLU', 'MEMA', 'UNKNOWN'],
                width='small'
            ),
            'marker_type': st.column_config.TextColumn('Type', width='medium'),
            'hit_count': st.column_config.NumberColumn('Hits', width='small'),
            'conversation_count': st.column_config.NumberColumn('Conversations', width='small'),
            'activity_rate': st.column_config.NumberColumn(
                'Activity Rate',
                format="%.3f",
                width='small'
            )
        },
        disabled=display_columns  # Make read-only
    )
    
    # Show selection info
    st.info(f"📊 Showing {len(markers_df)} markers")

def render_marker_statistics(markers_df: pd.DataFrame):
    """Render marker statistics and insights"""
    
    st.markdown("#### 📈 Statistics")
    
    if markers_df.empty:
        return
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_markers = len(markers_df)
        st.metric("Total Markers", f"{total_markers:,}")
    
    with col2:
        if 'hit_count' in markers_df.columns:
            total_hits = markers_df['hit_count'].sum()
            st.metric("Total Hits", f"{total_hits:,}")
    
    with col3:
        if 'hit_count' in markers_df.columns and len(markers_df) > 0:
            avg_hits = markers_df['hit_count'].mean()
            st.metric("Avg Hits/Marker", f"{avg_hits:.1f}")
    
    with col4:
        if 'marker_category' in markers_df.columns:
            categories = markers_df['marker_category'].nunique()
            st.metric("Active Categories", categories)
    
    # Category breakdown
    if 'marker_category' in markers_df.columns:
        st.markdown("##### Category Breakdown")
        
        category_stats = markers_df.groupby('marker_category').agg({
            'marker_id': 'count',
            'hit_count': 'sum' if 'hit_count' in markers_df.columns else 'count'
        }).rename(columns={
            'marker_id': 'marker_count',
            'hit_count': 'total_hits'
        })
        
        # Display as horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=category_stats.index,
                x=category_stats['marker_count'],
                orientation='h',
                marker=dict(
                    color=['#FF8C00', '#FFD700', '#FFA500', '#FF6347'][:len(category_stats)],
                    opacity=0.8
                ),
                text=category_stats['marker_count'],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Markers by Category",
            xaxis_title="Number of Markers",
            yaxis_title="Category",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_marker_architecture(markers_df: pd.DataFrame):
    """Render marker architecture visualization"""
    
    st.markdown("#### 🏗️ Marker Architecture")
    
    if 'marker_category' not in markers_df.columns:
        st.info("No category information available for architecture visualization")
        return
    
    # Architecture flow diagram
    category_counts = markers_df['marker_category'].value_counts()
    
    # Create architecture flow
    fig = go.Figure()
    
    # Define positions and colors for each level
    levels = ['ATO', 'SEM', 'CLU', 'MEMA']
    colors = ['#FF8C00', '#FFD700', '#FFA500', '#FF6347']
    positions = [(0.2, 0.5), (0.4, 0.7), (0.6, 0.5), (0.8, 0.3)]
    
    for i, level in enumerate(levels):
        if level in category_counts:
            count = category_counts[level]
            x, y = positions[i]
            
            # Add circle for each level
            fig.add_shape(
                type="circle",
                xref="paper", yref="paper",
                x0=x-0.05, y0=y-0.1,
                x1=x+0.05, y1=y+0.1,
                fillcolor=colors[i],
                opacity=0.7,
                line_color=colors[i]
            )
            
            # Add text
            fig.add_annotation(
                x=x, y=y,
                text=f"{level}<br>{count}",
                showarrow=False,
                font=dict(color="white", size=12, family="Arial Black"),
                xref="paper", yref="paper"
            )
            
            # Add flow arrows (except for last level)
            if i < len(levels) - 1 and i < len(positions) - 1:
                x_next, y_next = positions[i + 1]
                fig.add_annotation(
                    x=x_next - 0.02, y=y_next,
                    ax=x + 0.02, ay=y,
                    arrowhead=2, arrowsize=1, arrowwidth=2,
                    arrowcolor=colors[i],
                    xref="paper", yref="paper",
                    axref="paper", ayref="paper"
                )
    
    fig.update_layout(
        title="Marker Architecture Flow (ATO → SEM → CLU → MEMA)",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Architecture compliance check
    render_architecture_compliance(category_counts)

def render_architecture_compliance(category_counts: pd.Series):
    """Render architecture compliance analysis"""
    
    st.markdown("##### 🔍 Architecture Compliance")
    
    compliance_checks = []
    
    # Check if all levels are represented
    required_levels = ['ATO', 'SEM', 'CLU', 'MEMA']
    missing_levels = [level for level in required_levels if level not in category_counts]
    
    if missing_levels:
        compliance_checks.append({
            'check': 'Complete Architecture',
            'status': '⚠️',
            'message': f'Missing levels: {", ".join(missing_levels)}'
        })
    else:
        compliance_checks.append({
            'check': 'Complete Architecture',
            'status': '✅',
            'message': 'All marker levels present'
        })
    
    # Check SEM to ATO ratio
    ato_count = category_counts.get('ATO', 0)
    sem_count = category_counts.get('SEM', 0)
    
    if sem_count > 0:
        if ato_count >= 2 * sem_count:
            compliance_checks.append({
                'check': 'SEM Composition',
                'status': '✅',
                'message': f'Sufficient ATOs for SEM composition ({ato_count} ATO, {sem_count} SEM)'
            })
        else:
            compliance_checks.append({
                'check': 'SEM Composition',
                'status': '⚠️',
                'message': f'May need more ATOs for proper SEM composition ({ato_count} ATO, {sem_count} SEM)'
            })
    
    # Display compliance results
    for check in compliance_checks:
        st.write(f"{check['status']} **{check['check']}**: {check['message']}")
