# Contributing to CS2 AI Coach

Thank you for your interest in contributing to CS2 AI Coach.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `python -m pytest tests/ -v`

## Code Standards

- Follow PEP 8 style guidelines
- Add type hints for function signatures
- Write docstrings for public methods
- Include unit tests for new features

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Update documentation if needed
5. Submit PR with description of changes

## Reporting Issues

- Use GitHub Issues for bug reports
- Include demo file (if applicable) and expected vs actual behavior
- Provide Python version and OS information

## Rating System Changes

Changes to the calibration system require:
- Justification with real demo data
- Before/after comparison for affected players
- Unit tests for new penalty/cap logic
