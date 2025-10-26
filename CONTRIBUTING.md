# Contributing to CalHacks

Thank you for your interest in contributing to CalHacks! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for client development)
- Git

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/calhacks.git
   cd calhacks
   ```

3. Set up the Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

4. Set up the client environment:
   ```bash
   cd client
   npm install
   cd ..
   ```

## Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards below

3. Test your changes:
   ```bash
   # Python tests
   pytest
   
   # Client linting
   cd client && npm run lint
   ```

4. Commit your changes with conventional commit messages:
   ```bash
   git commit -m "feat(scope): add new feature"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request

## Coding Standards

### Python

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use meaningful variable and function names

### JavaScript/TypeScript

- Use ESLint configuration
- Prefer TypeScript over JavaScript when possible
- Use meaningful variable and function names
- Write JSDoc comments for public functions

## Commit Message Format

We use conventional commits:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

Examples:
- `feat(xrpl): add multisig support`
- `fix(client): resolve wallet connection issue`
- `docs(readme): update installation instructions`

## Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting PR
- Add integration tests for complex features

## Code Review

All contributions require code review. Please:

- Review your own code before submitting
- Be responsive to review feedback
- Keep PRs focused and reasonably sized
- Update documentation as needed

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Ask in the project discussions
- Contact the maintainers

Thank you for contributing!