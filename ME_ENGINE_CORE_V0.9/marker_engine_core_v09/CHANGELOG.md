# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-10

### Added
- Initial release of Marker Engine
- Complete marker detection system with YAML-based definitions
- Activation engine with support for ANY, ALL, AT_LEAST, WEIGHTED_AND rules
- Multi-dimensional scoring engine with category weights
- Drift analysis with threshold-based event emission
- FastAPI-based REST service with comprehensive endpoints
- Deterministic output validation system
- Comprehensive test suite with end-to-end testing
- Docker containerization support
- CI/CD pipeline with GitHub Actions
- Complete documentation and API reference

### Features
- Pattern-based marker detection using regex
- Sliding window conversation analysis
- Evidence cascade tracking for activation rules
- Category-based scoring with severity multipliers
- Threshold-based drift monitoring
- RESTful API with OpenAPI documentation
- Health checks and metrics endpoints
- Write-once artifact persistence
- Comprehensive logging and error handling

### Technical Details
- Python 3.9+ support
- FastAPI for API framework
- PyYAML for configuration
- NumPy for numerical computations
- Pydantic for data validation
- Comprehensive type hints throughout

## [0.1.0] - 2025-09-01

### Added
- Basic marker engine core functionality
- Initial scoring system
- Basic API endpoints
- Initial test framework
- Project structure and documentation

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)
