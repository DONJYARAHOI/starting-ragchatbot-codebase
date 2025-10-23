#!/bin/bash
# Run all code quality checks with auto-fix

set -e

echo "🚀 Running all code quality checks with auto-fix..."
echo ""

echo "📋 Step 1/2: Auto-formatting"
echo "────────────────────────────"
uv run ruff format backend/
echo ""

echo "📋 Step 2/2: Linting with auto-fix"
echo "───────────────────────────────────"
uv run ruff check backend/ --fix
echo ""

echo "✅ All auto-fixes applied!"
echo "💡 Tip: Run ./scripts/quality.sh to verify all checks pass"
