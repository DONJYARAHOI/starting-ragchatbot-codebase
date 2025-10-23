#!/bin/bash
# Run linting checks with automatic fixes

set -e

echo "🔧 Running ruff linter with auto-fix..."
uv run ruff check backend/ --fix

echo "✅ Linting and auto-fix complete!"
