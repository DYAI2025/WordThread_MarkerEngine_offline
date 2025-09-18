import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List
import json

def render_evidence_panel(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]):
    """Render evidence panel displaying marker details, weights, and scoring windows"""
    
    st.markdown("### 🔍 Evidence & Provenance")
    st.markdown("Detailed analysis of marker evidence, weights, scoring windows, and data provenance.")
    
    if not analysis_data and not sqlite_data:
        st.info("🔍 No evidence data available. Please upload data files.")
        return
    
    # Prepare evidence data
    evidence_data = prepare_evidence_data(analysis_data, sqlite_data)
    
    # Render evidence sections
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_marker_evidence(evidence_data)
        render_scoring_windows(evidence_data)
    
    with col2:
        render_provenance_info(evidence_data)
        render_weight_analysis(evidence_data)

def prepare_evidence_data(analysis_data: Optional[Dict[str, Any]], sqlite_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Prepare evidence data from multiple sources"""
    
    evidence = {
        'markers': [],
        'weights': {},
        'scoring_windows': {},
        'provenance': {},
        'metadata': {}
    }
    
    # Extract evidence from analysis bundle
    if analysis_data:
        evidence['markers'] = extract_marker_evidence_from_bundle(analysis_data)
        evidence['weights'] = analysis_data.get('aggregates', {})
        evidence['scoring_windows'] = analysis_data.get('scores', {})
        evidence['provenance'] = analysis_data.get('provenance', {})
        evidence['metadata']['bundle_id'] = analysis_data.get('bundle', 'unknown')
        evidence['metadata']['context'] = analysis_data.get('context', {})
    
    # Extract evidence from SQLite data
    if sqlite_data:
        sqlite_evidence = extract_evidence_from_sqlite(sqlite_data)
        
        # Merge with existing evidence
        evidence['markers'].extend(sqlite_evidence.get('markers', []))
        evidence['weights'].update(sqlite_evidence.get('weights', {}))
        evidence['scoring_windows'].update(sqlite_evidence.get('scoring_windows', {}))
        evidence['provenance'].update(sqlite_evidence.get('provenance', {}))
    
    return evidence

def extract_marker_evidence_from_bundle(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract marker evidence from analysis bundle"""
    
    evidence_list = []
    
    if 'hits' in analysis_data:
        hits_df = pd.DataFrame(analysis_data['hits'])
        
        # Group hits by marker to create evidence entries
        for marker_id, group in hits_df.groupby('marker_id'):
            evidence_entry = {
                'marker_id': marker_id,
                'marker_category': categorize_marker(marker_id),
                'hit_count': len(group),
                'first_occurrence': group['ts'].min() if 'ts' in group.columns else None,
                'last_occurrence': group['ts'].max() if 'ts' in group.columns else None,
                'conversations': group['conv'].nunique() if 'conv' in group.columns else 0,
                'confidence_scores': extract_confidence_scores(group),
                'payload_summary': summarize_payloads(group)
            }
            
            evidence_list.append(evidence_entry)
    
    return evidence_list

def extract_evidence_from_sqlite(sqlite_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract evidence from SQLite data"""
    
    evidence = {
        'markers': [],
        'weights': {},
        'scoring_windows': {},
        'provenance': {}
    }
    
    if 'tables' not in sqlite_data:
        return evidence
    
    tables = sqlite_data['tables']
    
    # Extract marker evidence from hits table
    if 'hits' in tables:
        hits_df = pd.DataFrame(tables['hits'])
        
        if not hits_df.empty:
            for marker_id, group in hits_df.groupby('marker_id'):
                evidence_entry = {
                    'marker_id': marker_id,
                    'marker_category': categorize_marker(marker_id),
                    'hit_count': len(group),
                    'source': 'sqlite',
                    'table_info': 'hits'
                }
                evidence['markers'].append(evidence_entry)
    
    # Extract scoring information
    if 'scores' in tables:
        scores_df = pd.DataFrame(tables['scores'])
        if not scores_df.empty:
            evidence['scoring_windows'] = scores_df.to_dict('records')
    
    # Extract provenance information
    if 'provenance' in tables:
        prov_df = pd.DataFrame(tables['provenance'])
        if not prov_df.empty:
            evidence['provenance'] = prov_df.to_dict('records')
    
    return evidence

def categorize_marker(marker_id: str) -> str:
    """Categorize marker based on ID prefix"""
    if marker_id.startswith('ATO_'):
        return 'ATO'
    elif marker_id.startswith('SEM_'):
        return 'SEM'
    elif marker_id.startswith('CLU_'):
        return 'CLU'
    elif marker_id.startswith('MEMA_'):
        return 'MEMA'
    elif marker_id.startswith('CLU_INTUITION_'):
        return 'INTUITION'
    else:
        return 'UNKNOWN'

def extract_confidence_scores(group: pd.DataFrame) -> List[float]:
    """Extract confidence scores from hit group"""
    scores = []
    
    if 'payload' in group.columns:
        for payload in group['payload']:
            if isinstance(payload, dict) and 'confidence' in payload:
                scores.append(payload['confidence'])
    
    return scores

def summarize_payloads(group: pd.DataFrame) -> Dict[str, Any]:
    """Summarize payload information from hit group"""
    
    summary = {
        'total_payloads': 0,
        'payload_keys': set(),
        'avg_confidence': None
    }
    
    if 'payload' in group.columns:
        payloads = group['payload'].dropna()
        summary['total_payloads'] = len(payloads)
        
        confidence_scores = []
        for payload in payloads:
            if isinstance(payload, dict):
                summary['payload_keys'].update(payload.keys())
                if 'confidence' in payload:
                    confidence_scores.append(payload['confidence'])
        
        summary['payload_keys'] = list(summary['payload_keys'])
        
        if confidence_scores:
            summary['avg_confidence'] = sum(confidence_scores) / len(confidence_scores)
    
    return summary

def render_marker_evidence(evidence_data: Dict[str, Any]):
    """Render detailed marker evidence"""
    
    st.markdown("#### 📋 Marker Evidence")
    
    markers = evidence_data.get('markers', [])
    
    if not markers:
        st.info("No marker evidence available")
        return
    
    # Convert to DataFrame for display
    markers_df = pd.DataFrame(markers)
    
    # Marker selection
    if not markers_df.empty:
        selected_marker = st.selectbox(
            "Select Marker for Detailed Evidence",
            markers_df['marker_id'].tolist(),
            help="Choose a marker to view detailed evidence"
        )
        
        # Display detailed evidence for selected marker
        if selected_marker:
            marker_data = markers_df[markers_df['marker_id'] == selected_marker].iloc[0]
            
            # Evidence details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Hit Count", marker_data.get('hit_count', 'N/A'))
            
            with col2:
                st.metric("Category", marker_data.get('marker_category', 'Unknown'))
            
            with col3:
                conversations = marker_data.get('conversations', 0)
                st.metric("Conversations", conversations if conversations else 'N/A')
            
            # Confidence analysis
            if 'confidence_scores' in marker_data and marker_data['confidence_scores']:
                st.markdown("##### 📊 Confidence Analysis")
                
                confidence_scores = marker_data['confidence_scores']
                
                if confidence_scores:
                    conf_df = pd.DataFrame({'confidence': confidence_scores})
                    
                    fig = go.Figure(data=[
                        go.Histogram(
                            x=confidence_scores,
                            nbinsx=20,
                            marker=dict(
                                color='rgba(255,140,0,0.7)',
                                line=dict(color='rgba(255,140,0,1)', width=1)
                            )
                        )
                    ])
                    
                    fig.update_layout(
                        title="Confidence Score Distribution",
                        xaxis_title="Confidence Score",
                        yaxis_title="Frequency",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Confidence statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Mean", f"{conf_df['confidence'].mean():.3f}")
                    with col2:
                        st.metric("Median", f"{conf_df['confidence'].median():.3f}")
                    with col3:
                        st.metric("Std Dev", f"{conf_df['confidence'].std():.3f}")
                    with col4:
                        st.metric("Min/Max", f"{conf_df['confidence'].min():.2f}/{conf_df['confidence'].max():.2f}")
            
            # Payload summary
            if 'payload_summary' in marker_data:
                payload_summary = marker_data['payload_summary']
                
                if payload_summary and payload_summary.get('total_payloads', 0) > 0:
                    st.markdown("##### 📦 Payload Information")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Total Payloads:** {payload_summary.get('total_payloads', 0)}")
                        
                        if payload_summary.get('avg_confidence'):
                            st.write(f"**Average Confidence:** {payload_summary['avg_confidence']:.3f}")
                    
                    with col2:
                        payload_keys = payload_summary.get('payload_keys', [])
                        if payload_keys:
                            st.write("**Payload Keys:**")
                            for key in payload_keys[:5]:  # Show first 5 keys
                                st.write(f"• {key}")
                            if len(payload_keys) > 5:
                                st.write(f"... and {len(payload_keys) - 5} more")

def render_scoring_windows(evidence_data: Dict[str, Any]):
    """Render scoring windows and weight information"""
    
    st.markdown("#### ⚖️ Scoring Windows & Weights")
    
    scoring_windows = evidence_data.get('scoring_windows', {})
    weights = evidence_data.get('weights', {})
    
    if not scoring_windows and not weights:
        st.info("No scoring or weight information available")
        return
    
    # Display weights information
    if weights:
        st.markdown("##### 📏 Marker Weights")
        
        # Convert weights to displayable format
        weight_items = []
        for key, value in weights.items():
            if isinstance(value, (int, float)):
                weight_items.append({'Parameter': key, 'Value': value})
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)):
                        weight_items.append({'Parameter': f"{key}.{sub_key}", 'Value': sub_value})
        
        if weight_items:
            weights_df = pd.DataFrame(weight_items)
            
            # Display as table
            st.dataframe(weights_df, use_container_width=True, hide_index=True)
            
            # Weight distribution chart
            if len(weights_df) > 0:
                fig = go.Figure(data=[
                    go.Bar(
                        x=weights_df['Parameter'],
                        y=weights_df['Value'],
                        marker=dict(
                            color='rgba(255,140,0,0.7)',
                            line=dict(color='rgba(255,140,0,1)', width=1)
                        )
                    )
                ])
                
                fig.update_layout(
                    title="Weight Distribution",
                    xaxis_title="Parameter",
                    yaxis_title="Weight Value",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    xaxis_tickangle=-45,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Display scoring windows
    if scoring_windows:
        st.markdown("##### 🎯 Scoring Information")
        
        # Convert scoring windows to displayable format
        if isinstance(scoring_windows, dict):
            scoring_items = []
            for key, value in scoring_windows.items():
                if isinstance(value, (int, float)):
                    scoring_items.append({'Metric': key, 'Score': value})
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float)):
                            scoring_items.append({'Metric': f"{key}.{sub_key}", 'Score': sub_value})
            
            if scoring_items:
                scoring_df = pd.DataFrame(scoring_items)
                st.dataframe(scoring_df, use_container_width=True, hide_index=True)
        elif isinstance(scoring_windows, list):
            # Display as list of records
            scoring_df = pd.DataFrame(scoring_windows)
            st.dataframe(scoring_df, use_container_width=True, hide_index=True)

def render_provenance_info(evidence_data: Dict[str, Any]):
    """Render data provenance information"""
    
    st.markdown("#### 📜 Data Provenance")
    
    provenance = evidence_data.get('provenance', {})
    metadata = evidence_data.get('metadata', {})
    
    if not provenance and not metadata:
        st.info("No provenance information available")
        return
    
    # Display metadata
    if metadata:
        st.markdown("##### 📊 Metadata")
        
        for key, value in metadata.items():
            if isinstance(value, dict):
                st.write(f"**{key.replace('_', ' ').title()}:**")
                for sub_key, sub_value in value.items():
                    st.write(f"  • {sub_key}: {sub_value}")
            else:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    # Display provenance information
    if provenance:
        st.markdown("##### 🔗 Provenance Chain")
        
        if isinstance(provenance, dict):
            # Display provenance as key-value pairs
            for key, value in provenance.items():
                if isinstance(value, (str, int, float)):
                    st.write(f"**{key}:** {value}")
                elif isinstance(value, list):
                    st.write(f"**{key}:** {len(value)} items")
                    if len(value) <= 5:
                        for item in value:
                            st.write(f"  • {item}")
                    else:
                        for item in value[:3]:
                            st.write(f"  • {item}")
                        st.write(f"  ... and {len(value) - 3} more items")
        elif isinstance(provenance, list):
            # Display provenance as list of records
            for i, record in enumerate(provenance[:10]):  # Show first 10 records
                with st.expander(f"Provenance Record {i+1}"):
                    if isinstance(record, dict):
                        for key, value in record.items():
                            st.write(f"**{key}:** {value}")
                    else:
                        st.write(str(record))

def render_weight_analysis(evidence_data: Dict[str, Any]):
    """Render weight analysis and recommendations"""
    
    st.markdown("#### 🎯 Weight Analysis")
    
    weights = evidence_data.get('weights', {})
    markers = evidence_data.get('markers', [])
    
    if not weights and not markers:
        st.info("No weight data available for analysis")
        return
    
    # Analyze weight distribution
    weight_analysis = analyze_weights(weights, markers)
    
    if weight_analysis:
        # Display weight statistics
        st.markdown("##### 📈 Weight Statistics")
        
        if 'weight_stats' in weight_analysis:
            stats = weight_analysis['weight_stats']
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'total_weights' in stats:
                    st.metric("Total Parameters", stats['total_weights'])
                if 'avg_weight' in stats:
                    st.metric("Average Weight", f"{stats['avg_weight']:.3f}")
            
            with col2:
                if 'weight_range' in stats:
                    weight_range = stats['weight_range']
                    st.metric("Weight Range", f"{weight_range['min']:.3f} - {weight_range['max']:.3f}")
                if 'weight_variance' in stats:
                    st.metric("Weight Variance", f"{stats['weight_variance']:.3f}")
        
        # Display recommendations
        if 'recommendations' in weight_analysis:
            st.markdown("##### 💡 Recommendations")
            
            for rec in weight_analysis['recommendations']:
                st.info(f"• {rec}")
    
    # Display intuition marker information if available
    render_intuition_markers(markers)

def analyze_weights(weights: Dict[str, Any], markers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze weight distribution and generate insights"""
    
    analysis = {
        'weight_stats': {},
        'recommendations': []
    }
    
    # Extract numeric weights
    numeric_weights = []
    weight_names = []
    
    def extract_numeric_values(data, prefix=""):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, (int, float)):
                numeric_weights.append(value)
                weight_names.append(full_key)
            elif isinstance(value, dict):
                extract_numeric_values(value, full_key)
    
    if isinstance(weights, dict):
        extract_numeric_values(weights)
    
    if numeric_weights:
        # Calculate statistics
        analysis['weight_stats'] = {
            'total_weights': len(numeric_weights),
            'avg_weight': sum(numeric_weights) / len(numeric_weights),
            'weight_range': {
                'min': min(numeric_weights),
                'max': max(numeric_weights)
            },
            'weight_variance': pd.Series(numeric_weights).var()
        }
        
        # Generate recommendations
        avg_weight = analysis['weight_stats']['avg_weight']
        weight_variance = analysis['weight_stats']['weight_variance']
        
        if weight_variance > avg_weight:
            analysis['recommendations'].append(
                "High weight variance detected. Consider normalizing weights for consistent scoring."
            )
        
        if analysis['weight_stats']['weight_range']['max'] > 10 * analysis['weight_stats']['weight_range']['min']:
            analysis['recommendations'].append(
                "Large weight range detected. Verify that weight scales are appropriate."
            )
        
        if len(numeric_weights) < 5:
            analysis['recommendations'].append(
                "Limited weight parameters found. Consider expanding scoring criteria."
            )
    
    # Analyze marker categories
    if markers:
        marker_categories = {}
        for marker in markers:
            category = marker.get('marker_category', 'Unknown')
            marker_categories[category] = marker_categories.get(category, 0) + 1
        
        if len(marker_categories) < 4:  # Missing some of ATO, SEM, CLU, MEMA
            analysis['recommendations'].append(
                "Not all marker categories are represented. Consider expanding marker coverage."
            )
    
    if not analysis['recommendations']:
        analysis['recommendations'].append(
            "Weight configuration appears balanced and appropriate."
        )
    
    return analysis

def render_intuition_markers(markers: List[Dict[str, Any]]):
    """Render intuition marker information"""
    
    intuition_markers = [m for m in markers if m.get('marker_category') == 'INTUITION']
    
    if not intuition_markers:
        return
    
    st.markdown("##### 🧠 Intuition Markers")
    st.markdown("Intuition-CLUs with runtime states and telemetry.")
    
    for marker in intuition_markers:
        with st.expander(f"🧠 {marker['marker_id']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Hit Count:** {marker.get('hit_count', 'N/A')}")
                st.write(f"**Conversations:** {marker.get('conversations', 'N/A')}")
            
            with col2:
                # Simulated state information (would come from actual data)
                st.write("**Runtime State:** provisional → confirmed")
                st.write("**Multiplier:** 1.0")
                
                # Show confidence progression if available
                if 'confidence_scores' in marker and marker['confidence_scores']:
                    avg_confidence = sum(marker['confidence_scores']) / len(marker['confidence_scores'])
                    st.write(f"**Avg Confidence:** {avg_confidence:.3f}")
