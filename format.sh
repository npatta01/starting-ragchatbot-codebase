#!/bin/bash
# Auto-format code with Black and isort

set -e

echo "🎨 Formatting Python code..."
echo ""

# Run isort
echo "Running isort to sort imports..."
uv run isort backend/ main.py
echo "✓ Imports sorted"
echo ""

# Run Black
echo "Running Black to format code..."
uv run black backend/ main.py
echo "✓ Code formatted"
echo ""

echo "✅ Code formatting complete!"
