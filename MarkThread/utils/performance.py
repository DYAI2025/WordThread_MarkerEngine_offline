"""
Performance optimization utilities for WordThread Marker-Engine
Includes LTTB (Largest-Triangle-Three-Buckets) downsampling algorithm
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
import time
from functools import wraps


def lttb_downsample(data: pd.DataFrame, x_col: str, y_col: str, threshold: int = 5000) -> pd.DataFrame:
    """
    Largest-Triangle-Three-Buckets (LTTB) downsampling algorithm
    
    This algorithm preserves the visual characteristics of the data while reducing
    the number of points for better performance in large datasets.
    
    Args:
        data: DataFrame containing the time series data
        x_col: Name of the x-axis column (typically timestamp)
        y_col: Name of the y-axis column (typically values)
        threshold: Target number of points after downsampling
    
    Returns:
        Downsampled DataFrame with preserved visual characteristics
    """
    
    if len(data) <= threshold:
        return data.copy()
    
    # Sort data by x column
    sorted_data = data.sort_values(x_col).reset_index(drop=True)
    
    # Convert to numpy arrays for faster computation
    x_values = sorted_data[x_col].values
    y_values = sorted_data[y_col].values
    
    # Calculate bucket size
    bucket_size = (len(data) - 2) / (threshold - 2)
    
    # Always include first and last points
    sampled_indices = [0]
    
    # Calculate points for each bucket
    a = 0  # Initially a is the first point in the triangle
    
    for i in range(threshold - 2):
        # Calculate the range for this bucket
        avg_range_start = int((i + 1) * bucket_size) + 1
        avg_range_end = int((i + 2) * bucket_size) + 1
        avg_range_end = min(avg_range_end, len(x_values))
        
        # Calculate the average point of the next bucket (point c)
        avg_x = np.mean(x_values[avg_range_start:avg_range_end])
        avg_y = np.mean(y_values[avg_range_start:avg_range_end])
        
        # Get the range of the current bucket
        range_start = int(i * bucket_size) + 1
        range_end = int((i + 1) * bucket_size) + 1
        range_end = min(range_end, len(x_values))
        
        # Point A (the previous selected point)
        point_a_x = x_values[a]
        point_a_y = y_values[a]
        
        max_area = -1
        next_a = range_start
        
        # Find the point in the current bucket that creates the largest triangle
        for j in range(range_start, range_end):
            # Calculate triangle area
            area = abs(
                (point_a_x - avg_x) * (y_values[j] - point_a_y) -
                (point_a_x - x_values[j]) * (avg_y - point_a_y)
            ) * 0.5
            
            if area > max_area:
                max_area = area
                next_a = j
        
        sampled_indices.append(next_a)
        a = next_a  # This is the next a (chosen from current bucket)
    
    # Always include the last point
    sampled_indices.append(len(data) - 1)
    
    # Remove duplicates while preserving order
    sampled_indices = sorted(list(set(sampled_indices)))
    
    # Return the downsampled data
    return sorted_data.iloc[sampled_indices].copy()


def adaptive_downsample(data: pd.DataFrame, x_col: str, y_col: str, max_points: int = 5000) -> pd.DataFrame:
    """
    Adaptive downsampling that chooses the best strategy based on data characteristics
    
    Args:
        data: DataFrame containing the data
        x_col: Name of the x-axis column
        y_col: Name of the y-axis column
        max_points: Maximum number of points to return
    
    Returns:
        Downsampled DataFrame
    """
    
    if len(data) <= max_points:
        return data.copy()
    
    # For very large datasets, use LTTB
    if len(data) > max_points * 2:
        return lttb_downsample(data, x_col, y_col, max_points)
    
    # For moderately large datasets, use uniform sampling with some randomness
    else:
        step = len(data) // max_points
        indices = list(range(0, len(data), step))
        
        # Always include the last point
        if indices[-1] != len(data) - 1:
            indices.append(len(data) - 1)
        
        return data.iloc[indices[:max_points]].copy()


def optimize_time_series_data(data: pd.DataFrame, time_col: str, value_cols: List[str], max_points: int = 5000) -> pd.DataFrame:
    """
    Optimize time series data for visualization by downsampling multiple value columns
    
    Args:
        data: DataFrame containing time series data
        time_col: Name of the time column
        value_cols: List of value column names to downsample
        max_points: Maximum number of points per series
    
    Returns:
        Optimized DataFrame with downsampled data
    """
    
    if len(data) <= max_points:
        return data.copy()
    
    # Sort by time column
    sorted_data = data.sort_values(time_col).reset_index(drop=True)
    
    # For multiple value columns, we need to find a consensus sampling
    # Use the first value column as the primary for LTTB, then apply the same indices to others
    primary_col = value_cols[0]
    downsampled = lttb_downsample(sorted_data, time_col, primary_col, max_points)
    
    # Get the indices of the downsampled points
    downsampled_indices = downsampled.index.tolist()
    
    # Apply the same indices to get all columns
    result = sorted_data.iloc[downsampled_indices].copy()
    
    return result


def performance_timer(func):
    """Decorator to measure function execution time"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Store performance data in the result if it's a dict
        if isinstance(result, dict):
            if 'performance_metrics' not in result:
                result['performance_metrics'] = {}
            result['performance_metrics'][f'{func.__name__}_ms'] = execution_time
        
        return result
    
    return wrapper


def calculate_data_density(data: pd.DataFrame, time_col: str) -> Dict[str, float]:
    """
    Calculate data density metrics for performance optimization decisions
    
    Args:
        data: DataFrame containing time series data
        time_col: Name of the time column
    
    Returns:
        Dictionary with density metrics
    """
    
    if len(data) < 2:
        return {'density': 0, 'avg_interval': 0, 'total_span': 0}
    
    # Convert to pandas datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(data[time_col]):
        time_data = pd.to_datetime(data[time_col], unit='s', errors='coerce')
    else:
        time_data = data[time_col]
    
    time_data = time_data.dropna().sort_values()
    
    if len(time_data) < 2:
        return {'density': 0, 'avg_interval': 0, 'total_span': 0}
    
    # Calculate time span and average interval
    total_span = (time_data.iloc[-1] - time_data.iloc[0]).total_seconds()
    avg_interval = total_span / (len(time_data) - 1) if len(time_data) > 1 else 0
    
    # Calculate density (points per hour)
    density = len(time_data) / (total_span / 3600) if total_span > 0 else 0
    
    return {
        'density': density,
        'avg_interval': avg_interval,
        'total_span': total_span,
        'total_points': len(time_data)
    }


def should_downsample(data: pd.DataFrame, threshold: int = 10000) -> bool:
    """
    Determine if data should be downsampled based on size and characteristics
    
    Args:
        data: DataFrame to analyze
        threshold: Point threshold above which downsampling is recommended
    
    Returns:
        Boolean indicating if downsampling is recommended
    """
    
    return len(data) > threshold


def get_optimal_sample_size(data_size: int, max_points: int = 5000) -> int:
    """
    Calculate optimal sample size based on data size and performance requirements
    
    Args:
        data_size: Original data size
        max_points: Maximum desired points
    
    Returns:
        Optimal sample size
    """
    
    if data_size <= max_points:
        return data_size
    
    # Use logarithmic scaling for very large datasets
    if data_size > max_points * 10:
        return min(max_points, int(max_points * 0.8 + np.log10(data_size) * 100))
    
    return max_points


class PerformanceMonitor:
    """Monitor and track performance metrics for data processing operations"""
    
    def __init__(self):
        self.metrics = {
            'processing_times': [],
            'data_sizes': [],
            'downsample_ratios': [],
            'memory_usage': []
        }
    
    def record_processing(self, operation: str, duration_ms: float, data_size: int, 
                         downsample_ratio: float = 1.0):
        """Record performance metrics for a processing operation"""
        
        self.metrics['processing_times'].append({
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
        
        self.metrics['data_sizes'].append({
            'operation': operation,
            'size': data_size,
            'timestamp': time.time()
        })
        
        self.metrics['downsample_ratios'].append({
            'operation': operation,
            'ratio': downsample_ratio,
            'timestamp': time.time()
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        
        if not self.metrics['processing_times']:
            return {'status': 'no_data'}
        
        processing_times = [m['duration_ms'] for m in self.metrics['processing_times']]
        data_sizes = [m['size'] for m in self.metrics['data_sizes']]
        
        return {
            'avg_processing_time_ms': np.mean(processing_times),
            'max_processing_time_ms': np.max(processing_times),
            'min_processing_time_ms': np.min(processing_times),
            'avg_data_size': np.mean(data_sizes),
            'max_data_size': np.max(data_sizes),
            'total_operations': len(processing_times),
            'performance_score': self._calculate_performance_score()
        }
    
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        
        if not self.metrics['processing_times']:
            return 0
        
        processing_times = [m['duration_ms'] for m in self.metrics['processing_times']]
        avg_time = np.mean(processing_times)
        
        # Score based on processing time (lower is better)
        # < 100ms = excellent (90-100)
        # < 500ms = good (70-90)
        # < 1000ms = fair (50-70)
        # > 1000ms = poor (0-50)
        
        if avg_time < 100:
            return 90 + (100 - avg_time) / 10
        elif avg_time < 500:
            return 70 + (500 - avg_time) / 20
        elif avg_time < 1000:
            return 50 + (1000 - avg_time) / 25
        else:
            return max(0, 50 - (avg_time - 1000) / 100)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()