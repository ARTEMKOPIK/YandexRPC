# Contributing to WinYandexMusicRPC

Thank you for considering contributing to WinYandexMusicRPC! Here are some guidelines to help you get started.

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused on a single responsibility

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/WinYandexMusicRPC.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Install development dependencies: `pip install pytest pytest-cov`

## Running Tests

```bash
pytest tests/ -v --cov=.
```

## Pull Request Process

1. Create a new branch for your feature or bugfix
2. Make your changes following the code style guidelines
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request with a clear description of changes

## Reporting Issues

When reporting issues, please include:
- Python version
- Windows version
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any error messages or logs

## Feature Requests

Feature requests are welcome! Please provide:
- A clear description of the feature
- Why it would be useful
- Any examples of how it should work
