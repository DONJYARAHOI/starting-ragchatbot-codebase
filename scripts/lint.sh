#!/bin/bash
# Run linting checks with ruff

set -e

echo "🔍 Running ruff linter..."
uv run ruff check backend/ "$@"

echo "✅ Linting complete!"
