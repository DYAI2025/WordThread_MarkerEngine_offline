import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime, timedelta

def process_analysis_bundle(bundle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and enhance AnalysisBundle data for analysis"""
    
    processed_data = {
        'raw_bundle': bundle_data,
        'hits': [],
        'markers': {},
        'conversations': {},
        'temporal_features': {},
        'aggregated_metrics': {}
    }
    
    try:
        # Process hits data
        if 'hits' in bundle_data:
            processed_data['hits'] = process_hits_data(bundle_data['hits'])
            
            # Extract marker information
            processed_data['markers'] = extract_marker_information(processed_data['hits'])
            
            # Extract conversation patterns
            processed_data['conversations'] = extract_conversation_patterns(processed_data['hits'])
            
            # Calculate temporal features
            processed_data['temporal_features'] = calculate_temporal_features(processed_data['hits'])
            
            # Calculate aggregated metrics
            processed_data['aggregated_metrics'] = calculate_aggregated_metrics(processed_data['hits'])
        
        # Process additional bundle components
        processed_data['scores'] = bundle_data.get('scores', {})
        processed_data['aggregates'] = bundle_data.get('aggregates', {})
        processed_data['drift'] = bundle_data.get('drift', {})
        processed_data['provenance'] = bundle_data.get('provenance', {})
        processed_data['context'] = bundle_data.get('context', {})
        
        # Add processing metadata
        processed_data['processing_metadata'] = {
            'processed_at': datetime.now().isoformat(),
            'bundle_id': bundle_data.get('bundle', 'unknown'),
            'total_hits': len(processed_data['hits']),
            'processing_version': '1.0'
        }
        
    except Exception as e:
        processed_data['processing_error'] = str(e)
    
    return processed_data

def process_sqlite_data(sqlite_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process SQLite data for analysis"""
    
    processed_data = {
        'raw_data': sqlite_data,
        'hits': [],
        'messages': [],
        'scores': [],
        'aggregates': [],
        'drift_axes': [],
        'provenance': [],
        'processed_metrics': {}
    }
    
    try:
        tables = sqlite_data.get('tables', {})
        
        # Process each table
        for table_name, table_data in tables.items():
            if table_name == 'hits':
                processed_data['hits'] = process_sqlite_hits(table_data)
            elif table_name == 'messages':
                processed_data['messages'] = process_sqlite_messages(table_data)
            elif table_name == 'scores':
                processed_data['scores'] = process_sqlite_scores(table_data)
            elif table_name == 'aggregates':
                processed_data['aggregates'] = process_sqlite_aggregates(table_data)
            elif table_name == 'drift_axes':
                processed_data['drift_axes'] = process_sqlite_drift(table_data)
            elif table_name == 'provenance':
                processed_data['provenance'] = process_sqlite_provenance(table_data)
        
        # Calculate cross-table metrics
        processed_data['processed_metrics'] = calculate_sqlite_metrics(processed_data)
        
        # Add processing metadata
        processed_data['processing_metadata'] = {
            'processed_at': datetime.now().isoformat(),
            'source_tables': list(tables.keys()),
            'total_records': sum(len(table_data) for table_data in tables.values()),
            'processing_version': '1.0'
        }
        
    except Exception as e:
        processed_data['processing_error'] = str(e)
    
    return processed_data

def process_hits_data(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process and enhance hits data"""
    
    processed_hits = []
    
    for hit in hits:
        processed_hit = hit.copy()
        
        # Add derived fields
        if 'ts' in hit:
            processed_hit['datetime'] = datetime.fromtimestamp(hit['ts'])
            processed_hit['hour_of_day'] = processed_hit['datetime'].hour
            processed_hit['day_of_week'] = processed_hit['datetime'].weekday()
            processed_hit['day_name'] = processed_hit['datetime'].strftime('%A')
        
        # Categorize marker
        if 'marker_id' in hit:
            processed_hit['marker_category'] = categorize_marker(hit['marker_id'])
            processed_hit['marker_type'] = extract_marker_type(hit['marker_id'])
        
        # Process payload if present
        if 'payload' in hit and isinstance(hit['payload'], dict):
            processed_hit['confidence'] = hit['payload'].get('confidence')
            processed_hit['payload_keys'] = list(hit['payload'].keys())
            processed_hit['payload_size'] = len(hit['payload'])
        
        processed_hits.append(processed_hit)
    
    return processed_hits

def extract_marker_information(hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract detailed marker information from hits"""
    
    markers = {}
    
    for hit in hits:
        marker_id = hit.get('marker_id')
        if not marker_id:
            continue
        
        if marker_id not in markers:
            markers[marker_id] = {
                'marker_id': marker_id,
                'category': hit.get('marker_category', 'unknown'),
                'type': hit.get('marker_type', 'unknown'),
                'hit_count': 0,
                'first_seen': None,
                'last_seen': None,
                'conversations': set(),
                'confidence_scores': [],
                'temporal_distribution': {}
            }
        
        marker = markers[marker_id]
        marker['hit_count'] += 1
        
        # Update temporal information
        if 'datetime' in hit:
            hit_time = hit['datetime']
            if marker['first_seen'] is None or hit_time < marker['first_seen']:
                marker['first_seen'] = hit_time
            if marker['last_seen'] is None or hit_time > marker['last_seen']:
                marker['last_seen'] = hit_time
            
            # Track hourly distribution
            hour = hit.get('hour_of_day', 0)
            marker['temporal_distribution'][hour] = marker['temporal_distribution'].get(hour, 0) + 1
        
        # Track conversations
        if 'conv' in hit and hit['conv']:
            marker['conversations'].add(hit['conv'])
        
        # Collect confidence scores
        if 'confidence' in hit and hit['confidence'] is not None:
            marker['confidence_scores'].append(hit['confidence'])
    
    # Convert sets to counts and calculate statistics
    for marker_id, marker in markers.items():
        marker['conversation_count'] = len(marker['conversations'])
        marker['conversations'] = None  # Remove set for JSON serialization
        
        if marker['confidence_scores']:
            scores = marker['confidence_scores']
            marker['confidence_stats'] = {
                'mean': np.mean(scores),
                'median': np.median(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores)
            }
        
        # Calculate activity rate
        if marker['first_seen'] and marker['last_seen']:
            duration = (marker['last_seen'] - marker['first_seen']).total_seconds()
            marker['activity_rate'] = marker['hit_count'] / (duration + 1) if duration > 0 else marker['hit_count']
        
        # Convert datetime objects to strings for JSON serialization
        if marker['first_seen']:
            marker['first_seen'] = marker['first_seen'].isoformat()
        if marker['last_seen']:
            marker['last_seen'] = marker['last_seen'].isoformat()
    
    return markers

def extract_conversation_patterns(hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract conversation patterns and statistics"""
    
    conversations = {}
    
    for hit in hits:
        conv_id = hit.get('conv')
        if not conv_id:
            continue
        
        if conv_id not in conversations:
            conversations[conv_id] = {
                'conversation_id': conv_id,
                'hit_count': 0,
                'markers': set(),
                'first_activity': None,
                'last_activity': None,
                'duration_seconds': 0,
                'marker_categories': set()
            }
        
        conv = conversations[conv_id]
        conv['hit_count'] += 1
        
        # Track markers and categories
        if 'marker_id' in hit:
            conv['markers'].add(hit['marker_id'])
        if 'marker_category' in hit:
            conv['marker_categories'].add(hit['marker_category'])
        
        # Track temporal span
        if 'datetime' in hit:
            hit_time = hit['datetime']
            if conv['first_activity'] is None or hit_time < conv['first_activity']:
                conv['first_activity'] = hit_time
            if conv['last_activity'] is None or hit_time > conv['last_activity']:
                conv['last_activity'] = hit_time
    
    # Calculate final statistics
    for conv_id, conv in conversations.items():
        conv['unique_markers'] = len(conv['markers'])
        conv['unique_categories'] = len(conv['marker_categories'])
        
        # Calculate duration
        if conv['first_activity'] and conv['last_activity']:
            conv['duration_seconds'] = (conv['last_activity'] - conv['first_activity']).total_seconds()
        
        # Convert sets and datetime objects for JSON serialization
        conv['markers'] = list(conv['markers'])
        conv['marker_categories'] = list(conv['marker_categories'])
        
        if conv['first_activity']:
            conv['first_activity'] = conv['first_activity'].isoformat()
        if conv['last_activity']:
            conv['last_activity'] = conv['last_activity'].isoformat()
    
    return conversations

def calculate_temporal_features(hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate temporal features and patterns"""
    
    temporal_features = {
        'hourly_distribution': {},
        'daily_distribution': {},
        'activity_peaks': [],
        'quiet_periods': [],
        'temporal_statistics': {}
    }
    
    if not hits:
        return temporal_features
    
    # Extract timestamps
    timestamps = []
    hourly_counts = {}
    daily_counts = {}
    
    for hit in hits:
        if 'datetime' in hit:
            dt = hit['datetime']
            timestamps.append(dt)
            
            # Count by hour
            hour = dt.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            # Count by day
            day = dt.strftime('%Y-%m-%d')
            daily_counts[day] = daily_counts.get(day, 0) + 1
    
    temporal_features['hourly_distribution'] = hourly_counts
    temporal_features['daily_distribution'] = daily_counts
    
    if timestamps:
        # Calculate basic statistics
        timestamps.sort()
        total_span = (timestamps[-1] - timestamps[0]).total_seconds()
        
        temporal_features['temporal_statistics'] = {
            'start_time': timestamps[0].isoformat(),
            'end_time': timestamps[-1].isoformat(),
            'total_span_hours': total_span / 3600,
            'total_hits': len(timestamps),
            'average_rate_per_hour': len(timestamps) / (total_span / 3600) if total_span > 0 else 0
        }
        
        # Identify activity peaks (hours with above-average activity)
        if hourly_counts:
            avg_hourly = np.mean(list(hourly_counts.values()))
            peaks = [hour for hour, count in hourly_counts.items() if count > avg_hourly * 1.5]
            temporal_features['activity_peaks'] = sorted(peaks)
            
            # Identify quiet periods (hours with below-average activity)
            quiet = [hour for hour, count in hourly_counts.items() if count < avg_hourly * 0.5]
            temporal_features['quiet_periods'] = sorted(quiet)
    
    return temporal_features

def calculate_aggregated_metrics(hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregated metrics from hits data"""
    
    metrics = {
        'total_hits': len(hits),
        'unique_markers': 0,
        'unique_conversations': 0,
        'marker_category_distribution': {},
        'confidence_statistics': {},
        'activity_statistics': {}
    }
    
    if not hits:
        return metrics
    
    # Count unique values
    unique_markers = set()
    unique_conversations = set()
    category_counts = {}
    confidence_scores = []
    
    for hit in hits:
        if 'marker_id' in hit:
            unique_markers.add(hit['marker_id'])
        
        if 'conv' in hit and hit['conv']:
            unique_conversations.add(hit['conv'])
        
        if 'marker_category' in hit:
            category = hit['marker_category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        if 'confidence' in hit and hit['confidence'] is not None:
            confidence_scores.append(hit['confidence'])
    
    metrics['unique_markers'] = len(unique_markers)
    metrics['unique_conversations'] = len(unique_conversations)
    metrics['marker_category_distribution'] = category_counts
    
    # Calculate confidence statistics
    if confidence_scores:
        metrics['confidence_statistics'] = {
            'count': len(confidence_scores),
            'mean': float(np.mean(confidence_scores)),
            'median': float(np.median(confidence_scores)),
            'std': float(np.std(confidence_scores)),
            'min': float(np.min(confidence_scores)),
            'max': float(np.max(confidence_scores)),
            'percentiles': {
                '25': float(np.percentile(confidence_scores, 25)),
                '75': float(np.percentile(confidence_scores, 75)),
                '90': float(np.percentile(confidence_scores, 90))
            }
        }
    
    # Calculate activity statistics
    if metrics['unique_conversations'] > 0:
        metrics['activity_statistics'] = {
            'hits_per_conversation': metrics['total_hits'] / metrics['unique_conversations'],
            'markers_per_conversation': metrics['unique_markers'] / metrics['unique_conversations'],
            'conversation_diversity': metrics['unique_conversations'] / metrics['total_hits']
        }
    
    return metrics

def process_sqlite_hits(hits_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process hits data from SQLite"""
    
    processed_hits = []
    
    for hit in hits_data:
        processed_hit = hit.copy()
        
        # Convert timestamp if present
        if 'ts' in hit:
            try:
                processed_hit['datetime'] = datetime.fromtimestamp(hit['ts'])
                processed_hit['hour_of_day'] = processed_hit['datetime'].hour
                processed_hit['day_of_week'] = processed_hit['datetime'].weekday()
            except (ValueError, TypeError):
                pass
        
        # Categorize marker
        if 'marker_id' in hit:
            processed_hit['marker_category'] = categorize_marker(hit['marker_id'])
        
        processed_hits.append(processed_hit)
    
    return processed_hits

def process_sqlite_messages(messages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process messages data from SQLite"""
    
    processed_messages = []
    
    for message in messages_data:
        processed_message = message.copy()
        
        # Convert timestamp if present
        if 'timestamp' in message:
            try:
                processed_message['datetime'] = datetime.fromtimestamp(message['timestamp'])
            except (ValueError, TypeError):
                pass
        
        processed_messages.append(processed_message)
    
    return processed_messages

def process_sqlite_scores(scores_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process scores data from SQLite"""
    return scores_data  # Return as-is for now

def process_sqlite_aggregates(aggregates_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process aggregates data from SQLite"""
    return aggregates_data  # Return as-is for now

def process_sqlite_drift(drift_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process drift axes data from SQLite"""
    return drift_data  # Return as-is for now

def process_sqlite_provenance(provenance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process provenance data from SQLite"""
    return provenance_data  # Return as-is for now

def calculate_sqlite_metrics(processed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate cross-table metrics from SQLite data"""
    
    metrics = {
        'table_summary': {},
        'data_quality': {},
        'relationships': {}
    }
    
    # Table summary
    for table_name in ['hits', 'messages', 'scores', 'aggregates', 'drift_axes', 'provenance']:
        if table_name in processed_data:
            table_data = processed_data[table_name]
            metrics['table_summary'][table_name] = {
                'record_count': len(table_data),
                'has_data': len(table_data) > 0
            }
    
    # Data quality checks
    hits = processed_data.get('hits', [])
    if hits:
        hit_quality = analyze_data_quality(hits)
        metrics['data_quality']['hits'] = hit_quality
    
    # Relationship analysis
    messages = processed_data.get('messages', [])
    if hits and messages:
        relationship_analysis = analyze_table_relationships(hits, messages)
        metrics['relationships']['hits_messages'] = relationship_analysis
    
    return metrics

def analyze_data_quality(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze data quality for a given dataset"""
    
    quality = {
        'completeness': {},
        'consistency': {},
        'validity': {}
    }
    
    if not data:
        return quality
    
    total_records = len(data)
    
    # Analyze completeness
    field_completeness = {}
    for record in data:
        for field, value in record.items():
            if field not in field_completeness:
                field_completeness[field] = {'total': 0, 'non_null': 0}
            
            field_completeness[field]['total'] += 1
            if value is not None and value != '':
                field_completeness[field]['non_null'] += 1
    
    for field, stats in field_completeness.items():
        quality['completeness'][field] = stats['non_null'] / stats['total']
    
    # Analyze consistency (basic checks)
    marker_ids = [record.get('marker_id') for record in data if record.get('marker_id')]
    if marker_ids:
        unique_marker_patterns = set()
        for marker_id in marker_ids:
            if '_' in marker_id:
                pattern = marker_id.split('_')[0]
                unique_marker_patterns.add(pattern)
        
        quality['consistency']['marker_pattern_consistency'] = len(unique_marker_patterns)
    
    return quality

def analyze_table_relationships(hits: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze relationships between hits and messages tables"""
    
    relationships = {
        'conversation_overlap': 0,
        'temporal_alignment': False,
        'common_fields': []
    }
    
    # Find common conversation IDs
    hit_conversations = set(hit.get('conv') for hit in hits if hit.get('conv'))
    message_conversations = set(msg.get('conversation_id') for msg in messages if msg.get('conversation_id'))
    
    overlap = hit_conversations.intersection(message_conversations)
    relationships['conversation_overlap'] = len(overlap)
    
    # Check temporal alignment
    hit_times = [hit.get('ts') for hit in hits if hit.get('ts')]
    message_times = [msg.get('timestamp') for msg in messages if msg.get('timestamp')]
    
    if hit_times and message_times:
        hit_range = (min(hit_times), max(hit_times))
        message_range = (min(message_times), max(message_times))
        
        # Check if time ranges overlap
        relationships['temporal_alignment'] = (
            hit_range[0] <= message_range[1] and message_range[0] <= hit_range[1]
        )
    
    # Find common fields
    if hits and messages:
        hit_fields = set(hits[0].keys()) if hits else set()
        message_fields = set(messages[0].keys()) if messages else set()
        relationships['common_fields'] = list(hit_fields.intersection(message_fields))
    
    return relationships

def categorize_marker(marker_id: str) -> str:
    """Categorize marker based on ID prefix"""
    if not marker_id:
        return 'unknown'
    
    if marker_id.startswith('ATO_'):
        return 'ATO'
    elif marker_id.startswith('SEM_'):
        return 'SEM'
    elif marker_id.startswith('CLU_'):
        if 'INTUITION' in marker_id:
            return 'INTUITION'
        return 'CLU'
    elif marker_id.startswith('MEMA_'):
        return 'MEMA'
    else:
        return 'unknown'

def extract_marker_type(marker_id: str) -> str:
    """Extract marker type from ID"""
    if not marker_id or '_' not in marker_id:
        return marker_id
    
    parts = marker_id.split('_')
    if len(parts) > 1:
        return '_'.join(parts[1:])
    
    return marker_id

def filter_data_by_timerange(data: List[Dict[str, Any]], start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    """Filter data by time range"""
    
    filtered_data = []
    
    for record in data:
        record_time = None
        
        # Try different timestamp fields
        if 'datetime' in record and isinstance(record['datetime'], datetime):
            record_time = record['datetime']
        elif 'ts' in record:
            try:
                record_time = datetime.fromtimestamp(record['ts'])
            except (ValueError, TypeError):
                continue
        
        if record_time and start_time <= record_time <= end_time:
            filtered_data.append(record)
    
    return filtered_data

def aggregate_data_by_interval(data: List[Dict[str, Any]], interval_minutes: int = 60) -> Dict[str, Any]:
    """Aggregate data by time intervals"""
    
    aggregated = {
        'intervals': {},
        'total_records': len(data),
        'interval_minutes': interval_minutes
    }
    
    for record in data:
        record_time = None
        
        if 'datetime' in record and isinstance(record['datetime'], datetime):
            record_time = record['datetime']
        elif 'ts' in record:
            try:
                record_time = datetime.fromtimestamp(record['ts'])
            except (ValueError, TypeError):
                continue
        
        if record_time:
            # Round to interval
            interval_start = record_time.replace(
                minute=(record_time.minute // interval_minutes) * interval_minutes,
                second=0,
                microsecond=0
            )
            interval_key = interval_start.isoformat()
            
            if interval_key not in aggregated['intervals']:
                aggregated['intervals'][interval_key] = {
                    'start_time': interval_key,
                    'record_count': 0,
                    'markers': set(),
                    'conversations': set()
                }
            
            interval_data = aggregated['intervals'][interval_key]
            interval_data['record_count'] += 1
            
            if 'marker_id' in record:
                interval_data['markers'].add(record['marker_id'])
            
            if 'conv' in record and record['conv']:
                interval_data['conversations'].add(record['conv'])
    
    # Convert sets to counts
    for interval_data in aggregated['intervals'].values():
        interval_data['unique_markers'] = len(interval_data['markers'])
        interval_data['unique_conversations'] = len(interval_data['conversations'])
        del interval_data['markers']
        del interval_data['conversations']
    
    return aggregated
