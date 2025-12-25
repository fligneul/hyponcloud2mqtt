# Contributing to hyponcloud2mqtt

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

See the [README.md](README.md#development) for development setup instructions.

## Commit Message Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic changelog generation and semantic versioning.

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature (triggers minor version bump)
- **fix**: A bug fix (triggers patch version bump)
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, whitespace, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **ci**: CI/CD configuration changes
- **build**: Changes to build system or dependencies

### Breaking Changes

Add `BREAKING CHANGE:` in the footer or append `!` after the type to trigger a major version bump:

```
feat!: remove support for Python 3.10

BREAKING CHANGE: Python 3.11+ is now required
```

### Examples

```bash
# Feature
git commit -m "feat: add support for MQTT QoS levels"

# Bug fix
git commit -m "fix: handle connection timeout gracefully"

# Documentation
git commit -m "docs: update installation instructions"

# Breaking change
git commit -m "feat!: change configuration file format to TOML"
```

### Scopes (Optional)

You can add a scope to provide more context:

```bash
git commit -m "feat(mqtt): add TLS certificate validation"
git commit -m "fix(config): validate port range correctly"
git commit -m "docs(readme): add troubleshooting section"
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make your changes** following the code style and documentation standards
4. **Update documentation**:
   - Update `README.md` if relevant
   - Update `config.yaml.example` if relevant
   - Update `.env.example` if relevant
5. **Add tests** for new functionality
6. **Run quality checks** to ensure everything passes:
   ```bash
   # Linting
   flake8 src tests

   # Type checking
   mypy src tests

   # Unit tests
   pytest

   # Integration tests (requires Docker)
   python scripts/run_integration_tests.py
   ```
7. **Commit** using conventional commits
8. **Push** to your fork
9. **Create a Pull Request** to the `main` branch

## Release Process

Releases are automated using [release-please](https://github.com/googleapis/release-please):

1. Commits to `main` trigger release-please
2. Release-please creates/updates a release PR with:
   - Updated CHANGELOG.md
   - Version bump in pyproject.toml
3. When the release PR is merged:
   - GitHub release is created automatically
   - Publish workflow is triggered (PyPI, Docker Hub)

### Version Bumping

- `feat:` commits → minor version bump (0.1.0 → 0.2.0)
- `fix:` commits → patch version bump (0.1.0 → 0.1.1)
- `BREAKING CHANGE:` → major version bump (0.1.0 → 1.0.0)

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Keep functions focused and small
- Write descriptive variable names
- Add docstrings for public functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage

## Questions?

Feel free to open an issue for questions or discussions!
