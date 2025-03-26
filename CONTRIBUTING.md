# Contributing to JSON Translation Pipeline

Thank you for your interest in contributing to the JSON Translation Pipeline! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct.

## How to Contribute

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`python -m unittest discover tests`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/json-translation-pipeline.git
   cd json-translation-pipeline
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your API keys and settings

## Testing

- Run all tests: `python -m unittest discover tests`
- Run with coverage: `python -m pytest --cov=. tests/`

## Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose
- Write clear, descriptive variable names

## Documentation

- Update the README.md if you add new features
- Add docstrings to all new functions and classes
- Update the API documentation if you modify existing functions

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the documentation if needed
3. The PR will be merged once you have the sign-off of at least one other developer

## Questions?

Feel free to open an issue for any questions or concerns. 