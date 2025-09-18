#!/usr/bin/env python3
"""
Drift Metrics - Erweiterte Metriken für Co-emergente Semantic Drift (CoSD)

Dieses Modul implementiert vier neue Drift-Metriken für die erweiterte
CoSD-Analyse: Home Base, Density, Variability und Rise Rate.

Alle Metriken sind eigenständig implementiert und verwenden eigene
mathematische Formulierungen ohne externe Abhängigkeiten.
"""

import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .cost_vector_math import CoSDVector, VectorOperations

logger = logging.getLogger(__name__)


@dataclass
class HomeBaseMetrics:
    """
    Metriken für den emotionalen/semantischen Grundzustand.
    
    Attributes:
        center_vector: Zentrum aller Vektoren als Durchschnitt
        stability_score: Stabilität des Grundzustands (0-1)
        deviation_radius: Radius der Abweichungen vom Zentrum
        consistency_factor: Konsistenz der Grundposition
    """
    center_vector: np.ndarray
    stability_score: float
    deviation_radius: float
    consistency_factor: float
    metadata: Dict[str, any]


@dataclass
class DensityMetrics:
    """
    Metriken für die Ballung von Drift/Markern über Zeit.
    
    Attributes:
        marker_density: Marker-Konzentration pro Zeiteinheit
        temporal_clustering: Zeitliche Clusterung von Markern
        density_trend: Trend der Dichte-Entwicklung
        peak_density: Maximale Dichte im Zeitraum
    """
    marker_density: float
    temporal_clustering: float
    density_trend: float
    peak_density: float
    density_timeline: List[float]
    metadata: Dict[str, any]


@dataclass
class VariabilityMetrics:
    """
    Metriken für die Schwankungsbreite der Drift.
    
    Attributes:
        standard_deviation: Standardabweichung der Drift-Vektoren
        variance_score: Varianz-Score der semantischen Bewegung
        fluctuation_range: Bereich der Fluktuationen
        stability_index: Stabilitäts-Index (invers zu Variabilität)
    """
    standard_deviation: float
    variance_score: float
    fluctuation_range: Tuple[float, float]
    stability_index: float
    variability_timeline: List[float]
    metadata: Dict[str, any]


@dataclass
class RiseRateMetrics:
    """
    Metriken für die Anstiegsgeschwindigkeit von Drift/Emotion.
    
    Attributes:
        average_rise_rate: Durchschnittliche Anstiegsrate
        peak_rise_rate: Maximale Anstiegsrate
        acceleration_pattern: Beschleunigungsmuster
        rise_trend: Trend der Anstiegsentwicklung
    """
    average_rise_rate: float
    peak_rise_rate: float
    acceleration_pattern: str
    rise_trend: float
    rise_timeline: List[float]
    metadata: Dict[str, any]


def calculate_home_base(vectors: List[CoSDVector]) -> HomeBaseMetrics:
    """
    Berechnet den emotionalen/semantischen Grundzustand (Home Base).
    
    Die Home Base repräsentiert das Zentrum aller semantischen Vektoren
    und gibt Auskunft über die Stabilität und Konsistenz der Grundposition.
    
    Mathematische Definition:
    - Center Vector: Arithmetisches Mittel aller Vektor-Dimensionen
    - Stability Score: Inverse der durchschnittlichen Abweichung vom Zentrum
    - Deviation Radius: Standardabweichung der Distanzen zum Zentrum
    - Consistency Factor: Verhältnis von stabilen zu instabilen Vektoren
    
    Args:
        vectors: Liste von CoSDVector-Objekten
        
    Returns:
        HomeBaseMetrics mit allen Grundzustand-Metriken
    """
    if not vectors:
        raise ValueError("Vector list cannot be empty")
    
    # Center Vector: Arithmetisches Mittel aller Vektoren
    all_dimensions = np.array([vec.dimensions for vec in vectors])
    center_vector = np.mean(all_dimensions, axis=0)
    
    # Berechne Distanzen zum Zentrum
    distances_to_center = []
    for vec in vectors:
        center_vec = CoSDVector(
            dimensions=center_vector,
            timestamp=vec.timestamp
        )
        dist = VectorOperations.euclidean_distance(vec, center_vec)
        distances_to_center.append(dist)
    
    # Stability Score: Inverse der durchschnittlichen Abweichung
    avg_deviation = np.mean(distances_to_center)
    max_possible_deviation = np.sqrt(len(center_vector))  # Maximale Distanz in n-dimensionalem Raum
    stability_score = max(0.0, 1.0 - (avg_deviation / max_possible_deviation))
    
    # Deviation Radius: Standardabweichung der Distanzen
    deviation_radius = np.std(distances_to_center)
    
    # Consistency Factor: Anteil der Vektoren nahe dem Zentrum
    threshold = np.percentile(distances_to_center, 75)  # 75% der Vektoren
    stable_vectors = sum(1 for dist in distances_to_center if dist <= threshold)
    consistency_factor = stable_vectors / len(vectors)
    
    return HomeBaseMetrics(
        center_vector=center_vector,
        stability_score=float(stability_score),
        deviation_radius=float(deviation_radius),
        consistency_factor=float(consistency_factor),
        metadata={
            'vector_count': len(vectors),
            'dimension_count': len(center_vector),
            'avg_deviation': float(avg_deviation),
            'max_deviation': float(max(distances_to_center))
        }
    )


def calculate_density(vectors: List[CoSDVector], time_window: int = 5) -> DensityMetrics:
    """
    Berechnet die Ballung von Drift/Markern über Zeit (Density).
    
    Die Density-Metrik misst, wie stark Marker und semantische Drift
    in bestimmten Zeiträumen konzentriert sind.
    
    Mathematische Definition:
    - Marker Density: Anzahl Marker pro Zeiteinheit
    - Temporal Clustering: Zeitliche Clusterung basierend auf Marker-Gewichten
    - Density Trend: Linearer Trend der Dichte-Entwicklung
    - Peak Density: Maximale Dichte im analysierten Zeitraum
    
    Args:
        vectors: Liste von CoSDVector-Objekten
        time_window: Zeitfenster in Minuten für Dichte-Berechnung
        
    Returns:
        DensityMetrics mit allen Dichte-Metriken
    """
    if len(vectors) < 2:
        return DensityMetrics(
            marker_density=0.0,
            temporal_clustering=0.0,
            density_trend=0.0,
            peak_density=0.0,
            density_timeline=[],
            metadata={'error': 'Insufficient vectors for density calculation'}
        )
    
    # Berechne Marker-Dichte pro Zeitfenster
    density_timeline = []
    total_markers = 0
    
    for i in range(0, len(vectors), max(1, len(vectors) // 10)):  # 10 Zeitfenster
        window_end = min(i + time_window, len(vectors))
        window_vectors = vectors[i:window_end]
        
        # Zähle Marker in diesem Zeitfenster
        window_markers = 0
        for vec in window_vectors:
            window_markers += len(vec.marker_weights)
            total_markers += len(vec.marker_weights)
        
        # Dichte = Marker pro Zeiteinheit
        time_span = (window_vectors[-1].timestamp - window_vectors[0].timestamp).total_seconds() / 60
        if time_span > 0:
            density = window_markers / time_span
        else:
            density = window_markers
        density_timeline.append(density)
    
    # Marker Density: Durchschnittliche Dichte
    marker_density = np.mean(density_timeline) if density_timeline else 0.0
    
    # Temporal Clustering: Wie stark sind Marker zeitlich gruppiert
    if len(density_timeline) > 1:
        clustering_variance = np.var(density_timeline)
        max_possible_variance = np.var([0] * (len(density_timeline) - 1) + [total_markers])
        temporal_clustering = min(1.0, clustering_variance / max_possible_variance) if max_possible_variance > 0 else 0.0
    else:
        temporal_clustering = 0.0
    
    # Density Trend: Linearer Trend der Dichte-Entwicklung
    if len(density_timeline) > 1:
        x = np.arange(len(density_timeline))
        slope, _ = np.polyfit(x, density_timeline, 1)
        density_trend = float(slope)
    else:
        density_trend = 0.0
    
    # Peak Density: Maximale Dichte
    peak_density = float(max(density_timeline)) if density_timeline else 0.0
    
    return DensityMetrics(
        marker_density=float(marker_density),
        temporal_clustering=float(temporal_clustering),
        density_trend=float(density_trend),
        peak_density=float(peak_density),
        density_timeline=density_timeline,
        metadata={
            'time_window_minutes': time_window,
            'total_markers': total_markers,
            'timeline_points': len(density_timeline)
        }
    )


def calculate_variability(vectors: List[CoSDVector]) -> VariabilityMetrics:
    """
    Berechnet die Schwankungsbreite der Drift (Variability).
    
    Die Variability-Metrik misst, wie stark die semantischen Vektoren
    um ihren Mittelwert schwanken und gibt Auskunft über die Stabilität.
    
    Mathematische Definition:
    - Standard Deviation: Standardabweichung der Vektor-Dimensionen
    - Variance Score: Normalisierte Varianz über alle Dimensionen
    - Fluctuation Range: Min/Max der Schwankungen
    - Stability Index: Inverser Stabilitäts-Score (0 = stabil, 1 = instabil)
    
    Args:
        vectors: Liste von CoSDVector-Objekten
        
    Returns:
        VariabilityMetrics mit allen Variabilitäts-Metriken
    """
    if not vectors:
        raise ValueError("Vector list cannot be empty")
    
    # Extrahiere alle Vektor-Dimensionen
    all_dimensions = np.array([vec.dimensions for vec in vectors])
    
    # Standard Deviation: Über alle Dimensionen
    std_per_dimension = np.std(all_dimensions, axis=0)
    standard_deviation = float(np.mean(std_per_dimension))
    
    # Variance Score: Normalisierte Varianz
    variance_per_dimension = np.var(all_dimensions, axis=0)
    max_possible_variance = np.var(np.random.uniform(-1, 1, all_dimensions.shape))
    variance_score = float(np.mean(variance_per_dimension) / max_possible_variance) if max_possible_variance > 0 else 0.0
    
    # Fluctuation Range: Min/Max der Schwankungen
    min_values = np.min(all_dimensions, axis=0)
    max_values = np.max(all_dimensions, axis=0)
    fluctuation_range = (float(np.min(min_values)), float(np.max(max_values)))
    
    # Stability Index: Invers zu Variabilität
    stability_index = max(0.0, 1.0 - variance_score)
    
    # Variability Timeline: Entwicklung der Variabilität über Zeit
    variability_timeline = []
    window_size = max(1, len(vectors) // 5)  # 5 Zeitfenster
    
    for i in range(0, len(vectors), window_size):
        window_vectors = vectors[i:i+window_size]
        if len(window_vectors) > 1:
            window_dimensions = np.array([vec.dimensions for vec in window_vectors])
            window_variance = np.mean(np.var(window_dimensions, axis=0))
            variability_timeline.append(float(window_variance))
        else:
            variability_timeline.append(0.0)
    
    return VariabilityMetrics(
        standard_deviation=standard_deviation,
        variance_score=variance_score,
        fluctuation_range=fluctuation_range,
        stability_index=stability_index,
        variability_timeline=variability_timeline,
        metadata={
            'vector_count': len(vectors),
            'dimension_count': len(vectors[0].dimensions),
            'std_per_dimension': std_per_dimension.tolist()
        }
    )


def calculate_rise_rate(vectors: List[CoSDVector]) -> RiseRateMetrics:
    """
    Berechnet die Anstiegsgeschwindigkeit von Drift/Emotion (Rise Rate).
    
    Die Rise Rate misst, wie schnell sich semantische Drift und emotionale
    Intensität über Zeit entwickeln.
    
    Mathematische Definition:
    - Average Rise Rate: Durchschnittliche Anstiegsrate pro Zeiteinheit
    - Peak Rise Rate: Maximale Anstiegsrate im Zeitraum
    - Acceleration Pattern: Muster der Beschleunigung (linear/exponentiell/oszillierend)
    - Rise Trend: Trend der Anstiegsentwicklung
    
    Args:
        vectors: Liste von CoSDVector-Objekten
        
    Returns:
        RiseRateMetrics mit allen Anstiegsraten-Metriken
    """
    if len(vectors) < 2:
        return RiseRateMetrics(
            average_rise_rate=0.0,
            peak_rise_rate=0.0,
            acceleration_pattern="insufficient_data",
            rise_trend=0.0,
            rise_timeline=[],
            metadata={'error': 'Insufficient vectors for rise rate calculation'}
        )
    
    # Berechne Anstiegsraten zwischen aufeinanderfolgenden Vektoren
    rise_rates = []
    rise_timeline = []
    
    for i in range(1, len(vectors)):
        # Magnitude-Änderung
        magnitude_change = vectors[i].magnitude - vectors[i-1].magnitude
        
        # Zeitdifferenz
        time_delta = (vectors[i].timestamp - vectors[i-1].timestamp).total_seconds()
        
        if time_delta > 0:
            # Rise Rate = Magnitude-Änderung pro Zeiteinheit
            rise_rate = magnitude_change / time_delta
            rise_rates.append(rise_rate)
            rise_timeline.append(float(rise_rate))
        else:
            rise_rates.append(0.0)
            rise_timeline.append(0.0)
    
    # Average Rise Rate
    average_rise_rate = float(np.mean(rise_rates)) if rise_rates else 0.0
    
    # Peak Rise Rate
    peak_rise_rate = float(max(rise_rates)) if rise_rates else 0.0
    
    # Rise Trend: Linearer Trend der Anstiegsraten
    if len(rise_rates) > 1:
        x = np.arange(len(rise_rates))
        slope, _ = np.polyfit(x, rise_rates, 1)
        rise_trend = float(slope)
    else:
        rise_trend = 0.0
    
    # Acceleration Pattern: Bestimme das Beschleunigungsmuster
    if len(rise_rates) >= 3:
        # Berechne Beschleunigung (Änderung der Rise Rate)
        accelerations = np.diff(rise_rates)
        
        # Bestimme Muster basierend auf Beschleunigung
        avg_acceleration = np.mean(accelerations)
        acc_variance = np.var(accelerations)
        
        if abs(avg_acceleration) < 0.1 and acc_variance < 0.1:
            acceleration_pattern = "linear"
        elif avg_acceleration > 0.1:
            acceleration_pattern = "exponential"
        elif avg_acceleration < -0.1:
            acceleration_pattern = "decelerating"
        elif acc_variance > 0.5:
            acceleration_pattern = "oscillating"
        else:
            acceleration_pattern = "stable"
    else:
        acceleration_pattern = "insufficient_data"
    
    return RiseRateMetrics(
        average_rise_rate=average_rise_rate,
        peak_rise_rate=peak_rise_rate,
        acceleration_pattern=acceleration_pattern,
        rise_trend=rise_trend,
        rise_timeline=rise_timeline,
        metadata={
            'vector_count': len(vectors),
            'time_span_seconds': (vectors[-1].timestamp - vectors[0].timestamp).total_seconds(),
            'magnitude_range': (min(vec.magnitude for vec in vectors), max(vec.magnitude for vec in vectors))
        }
    )


def calculate_all_drift_metrics(vectors: List[CoSDVector]) -> Dict[str, any]:
    """
    Berechnet alle vier Drift-Metriken in einem Aufruf.
    
    Args:
        vectors: Liste von CoSDVector-Objekten
        
    Returns:
        Dict mit allen Metriken: home_base, density, variability, rise_rate
    """
    try:
        home_base = calculate_home_base(vectors)
        density = calculate_density(vectors)
        variability = calculate_variability(vectors)
        rise_rate = calculate_rise_rate(vectors)
        
        return {
            'home_base': {
                'stability_score': home_base.stability_score,
                'deviation_radius': home_base.deviation_radius,
                'consistency_factor': home_base.consistency_factor,
                'metadata': home_base.metadata
            },
            'density': {
                'marker_density': density.marker_density,
                'temporal_clustering': density.temporal_clustering,
                'density_trend': density.density_trend,
                'peak_density': density.peak_density,
                'metadata': density.metadata
            },
            'variability': {
                'standard_deviation': variability.standard_deviation,
                'variance_score': variability.variance_score,
                'fluctuation_range': variability.fluctuation_range,
                'stability_index': variability.stability_index,
                'metadata': variability.metadata
            },
            'rise_rate': {
                'average_rise_rate': rise_rate.average_rise_rate,
                'peak_rise_rate': rise_rate.peak_rise_rate,
                'acceleration_pattern': rise_rate.acceleration_pattern,
                'rise_trend': rise_rate.rise_trend,
                'metadata': rise_rate.metadata
            }
        }
    except Exception as e:
        logger.error(f"Error calculating drift metrics: {e}")
        return {
            'error': str(e),
            'home_base': None,
            'density': None,
            'variability': None,
            'rise_rate': None
        } 