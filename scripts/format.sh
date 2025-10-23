#!/bin/bash
# Format code with ruff

set -e

echo "🎨 Formatting Python code with ruff..."
uv run ruff format backend/

echo "✅ Formatting complete!"
