# Contributing to Marker Engine

Thank you for your interest in contributing to Marker Engine! We welcome contributions from the community.

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## How to Contribute

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/marker-engine.git
cd marker-engine
```

### 2. Set up Development Environment
```bash
make dev-install
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 5. Run Quality Checks
```bash
make format
make type-check
make test
make validate
```

### 6. Commit Your Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

### 7. Create a Pull Request
- Push your branch to GitHub
- Create a pull request with a clear description
- Reference any related issues

## Development Guidelines

### Code Style
- Use Black for code formatting
- Use isort for import sorting
- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes

### Testing
- Write unit tests for all new functionality
- Aim for at least 80% code coverage
- Test edge cases and error conditions
- Use descriptive test names

### Documentation
- Update README.md for significant changes
- Add docstrings to all public APIs
- Update type hints for clarity
- Include examples in documentation

### Commit Messages
Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

## Project Structure

```
marker-engine/
├── _Marker_5.0/          # Marker definitions
├── DETECT_/              # Detector configurations
├── SCH_/                 # Schema definitions
├── api_service.py        # FastAPI application
├── marker_engine_core.py # Core engine logic
├── scoring_engine.py     # Scoring calculations
├── drift_axes.py         # Drift analysis
├── tests/                # Test files
├── docs/                 # Documentation
└── requirements.txt      # Dependencies
```

## Adding New Markers

1. Create a new YAML file in `_Marker_5.0/`
2. Follow the existing marker format
3. Test the marker with sample conversations
4. Add appropriate tests

## Adding New Features

1. Discuss the feature in an issue first
2. Implement the feature with tests
3. Update documentation
4. Ensure backward compatibility

## Reporting Issues

When reporting bugs:
- Use the issue template
- Include steps to reproduce
- Provide sample data if possible
- Include error messages and stack traces
- Specify your environment (Python version, OS, etc.)

## Questions

If you have questions:
- Check the documentation first
- Search existing issues
- Create a discussion if needed
- Contact the maintainers

Thank you for contributing to Marker Engine! 🎉
