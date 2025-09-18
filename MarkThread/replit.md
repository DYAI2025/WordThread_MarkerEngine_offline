# WordThread Marker-Engine Frontend

## Overview

A comprehensive frontend application for the WordThread Marker-Engine, built with Streamlit to provide real-time visualization and analysis of language pattern markers. The application supports offline-first operation via Electron with browser fallback functionality. It processes AnalysisBundle JSON files and SQLite databases to display interactive charts, drift analysis, marker evidence, and provenance tracking with the distinctive WordThread visual design featuring gradients, glows, and volumetric lighting effects.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Framework
- **Streamlit-based UI**: Modern web interface with custom CSS for WordThread branding
- **Component-based architecture**: Modular design with reusable UI components for different analysis views
- **Responsive design**: Custom CSS with orange gradient themes, glow effects, and volumetric lighting
- **Multi-runtime support**: Primary Electron (Node-FS) with browser fallback using file uploads

### Data Processing Pipeline
- **Validation layer**: Pydantic schemas for strict AnalysisBundle v1.0 and PromatraHandshake v0.2 validation
- **Multi-source ingestion**: Supports JSON AnalysisBundle files and SQLite databases from Dash-Out-Sys
- **Performance optimization**: LTTB (Largest-Triangle-Three-Buckets) downsampling algorithm for large datasets
- **Data transformation**: Comprehensive processing utilities for temporal analysis and marker aggregation

### Marker Architecture Implementation
- **Four-tier hierarchy**: ATO (Atomic) → SEM (Semantic) → CLU (Cluster) → MEMA (Meta) marker levels
- **Intuitions-CLU states**: Provisional → Confirmed → Decayed lifecycle with multipliers and telemetry
- **Bottom-up visualization**: UI presents marker meaning emergence from atomic observations through combinations
- **Schema compliance**: Strict validation against Lean-DB 3.4 conventions for marker structures

### Visualization Engine
- **Interactive charts**: Plotly-based time series, heatmaps, distribution plots, and correlation matrices
- **Performance monitoring**: Real-time FPS tracking, paint time metrics, and data processing performance
- **Multi-axis drift analysis**: Temporal pattern detection with statistical analysis and predictive insights
- **Evidence panels**: Detailed marker scoring windows, weights, and provenance tracking

### State Management
- **Session persistence**: Streamlit session state for view configurations and selected markers
- **Export capabilities**: PNG snapshot generation and JSON state export functionality
- **Real-time updates**: Dynamic filtering and selection with immediate visual feedback

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for the main UI
- **Plotly**: Interactive charting and visualization library
- **Pandas/NumPy**: Data processing and numerical computations
- **Pydantic**: Schema validation and data modeling

### Database and File Handling
- **SQLite3**: Native SQLite database connectivity
- **Pillow (PIL)**: Image processing for PNG export functionality
- **Base64**: File encoding/decoding for attachment handling

### Performance and Analytics
- **SciPy**: Statistical analysis and signal processing for drift detection
- **psutil**: System resource monitoring and performance metrics
- **functools**: Performance decorators and optimization utilities

### Validation Schemas
- **AnalysisBundle v1.0**: Strict schema validation for marker data bundles
- **PromatraHandshake v0.2**: Enhanced attachment processing and evidence handling
- **Marker Architecture**: ATO/SEM/CLU/MEMA hierarchy validation with composition rules

### File System Integration
- **pathlib**: Modern path handling for cross-platform compatibility
- **tempfile**: Temporary file operations for data processing
- **json**: JSON parsing and serialization for data exchange

### Styling and Branding
- **Google Fonts**: Inter font family for consistent typography
- **CSS Grid/Flexbox**: Responsive layout system with WordThread orange theme
- **Custom CSS**: Gradient backgrounds, glow effects, and volumetric lighting