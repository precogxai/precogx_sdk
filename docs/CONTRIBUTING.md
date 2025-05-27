# Contributing to PrecogX SDK

Thank you for your interest in contributing to PrecogX SDK! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/precogx/precogx-sdk.git
cd precogx-sdk
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run the formatters:
```bash
black .
isort .
flake8
mypy .
```

## Testing

1. Install test dependencies:
```bash
pip install -e ".[test]"
```

2. Run tests:
```bash
pytest
```

3. Run with coverage:
```bash
pytest --cov=precogx_sdk
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatters
5. Submit a pull request

## Documentation

- Update docstrings using Google style
- Update relevant documentation files
- Add examples if introducing new features

## Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create a release tag
4. Build and publish to PyPI

## Support

- GitHub Issues: [github.com/precogx/precogx-sdk/issues](https://github.com/precogx/precogx-sdk/issues)
- Email: dev@precogx.ai 