.PHONY: help install dev-install test test-cov test-verbose lint format type-check clean validate run-api run-dev docs build dist

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black + isort)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  clean        - Clean up cache files and build artifacts"
	@echo "  validate     - Run system validation"
	@echo "  run-api      - Run the FastAPI server"
	@echo "  run-dev      - Run the development server with auto-reload"
	@echo "  docs         - Build documentation"
	@echo "  build        - Build distribution packages"
	@echo "  dist         - Create source and wheel distributions"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -e ".[dev]"

# Testing
test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-verbose:
	pytest -v --tb=long

# Code Quality
lint:
	flake8 .

format:
	black .
	isort .

type-check:
	mypy .

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

# Validation
validate:
	python validate_system.py

# Running
run-api:
	python -m uvicorn api_service:app --host 0.0.0.0 --port 8000

run-dev:
	python -m uvicorn api_service:app --host 0.0.0.0 --port 8000 --reload

# Documentation
docs:
	sphinx-build -b html docs/ docs/_build/html

# Distribution
build:
	python -m build

dist: build
	twine check dist/*

# Development workflow
dev: dev-install format type-check test validate

# CI/CD simulation
ci: clean dev-install lint type-check test-cov validate
