#!/bin/bash
# Run all code quality checks

set -e

echo "🚀 Running all code quality checks..."
echo ""

echo "📋 Step 1/3: Formatting check"
echo "─────────────────────────────"
uv run ruff format backend/ --check
echo ""

echo "📋 Step 2/3: Linting check"
echo "──────────────────────────"
uv run ruff check backend/
echo ""

echo "📋 Step 3/3: Running tests"
echo "──────────────────────────"
uv run pytest backend/tests/ -v
echo ""

echo "✅ All quality checks passed!"
