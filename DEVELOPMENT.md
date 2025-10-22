# Development Guide

This document provides guidance on maintaining code quality in this project.

## Code Quality Tools

This project uses [Ruff](https://github.com/astral-sh/ruff) for both linting and formatting Python code. Ruff is an extremely fast Python linter and formatter written in Rust.

### Configuration

Code quality settings are configured in `pyproject.toml`:

- **Line length**: 120 characters
- **Target Python version**: 3.13
- **Quote style**: Double quotes
- **Indentation**: Spaces

### Quick Start

#### Format Code

```bash
./scripts/format.sh
```

This will auto-format all Python files in the `backend/` directory according to project standards.

#### Lint Code

Check for linting issues without fixing:

```bash
./scripts/lint.sh
```

Auto-fix linting issues:

```bash
./scripts/lint-fix.sh
```

#### Run All Quality Checks

Run formatting check, linting, and tests:

```bash
./scripts/quality.sh
```

Auto-fix formatting and linting issues:

```bash
./scripts/quality-fix.sh
```

## Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit.

### Installation

Install pre-commit hooks:

```bash
uv run pre-commit install
```

### Usage

After installation, the hooks run automatically on `git commit`. To run manually on all files:

```bash
uv run pre-commit run --all-files
```

### What Gets Checked

The pre-commit hooks will:

1. Remove trailing whitespace
2. Fix end-of-file issues
3. Check YAML syntax
4. Prevent large files from being committed
5. Check for merge conflicts
6. Run ruff linting with auto-fix
7. Run ruff formatting

## Manual Quality Commands

If you prefer to run commands directly:

### Format Code

```bash
uv run ruff format backend/
```

### Check Formatting (without changing files)

```bash
uv run ruff format backend/ --check
```

### Lint Code

```bash
uv run ruff check backend/
```

### Lint with Auto-fix

```bash
uv run ruff check backend/ --fix
```

### Run Tests

```bash
uv run pytest backend/tests/ -v
```

## Ruff Configuration Details

### Enabled Rules

The following rule categories are enabled:

- **E, W**: pycodestyle errors and warnings
- **F**: pyflakes (unused imports, variables, etc.)
- **I**: isort (import sorting)
- **B**: flake8-bugbear (common bugs)
- **C4**: flake8-comprehensions (better comprehensions)
- **UP**: pyupgrade (modern Python syntax)

### Ignored Rules

- **E501**: Line too long (handled by the formatter)

### Per-file Ignores

- **backend/app.py**: E402 (module level imports after warnings filter)
- **backend/tests/*.py**: F841 (allow unused variables in tests)

## Best Practices

1. **Before committing**: Run `./scripts/quality-fix.sh` to auto-fix issues
2. **During development**: Use `./scripts/lint.sh` to check for issues
3. **In CI/CD**: Run `./scripts/quality.sh` to verify all checks pass
4. **Format often**: Run `./scripts/format.sh` regularly to maintain consistency

## Troubleshooting

### Pre-commit hook fails

If the pre-commit hook fails:

1. Review the error messages
2. Run `./scripts/quality-fix.sh` to auto-fix issues
3. Review and commit the changes
4. Try committing again

### Ruff errors that can't be auto-fixed

Some issues require manual intervention:

- Unused variables or imports
- Complex code simplifications
- Type hint issues

Review the error message and fix manually, or use `# noqa: CODE` to ignore specific issues.

## IDE Integration

### VS Code

Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff):

```json
{
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

Configure Ruff as an external tool or use the [Ruff plugin](https://plugins.jetbrains.com/plugin/20574-ruff).

## Dependencies

Quality tools are installed as development dependencies:

```bash
uv sync
```

This installs:
- `ruff`: Linter and formatter
- `pre-commit`: Pre-commit hook framework
- `pytest`: Testing framework
