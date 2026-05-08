#!/bin/bash
# ==============================================================================
# BudgetWise Documentation Rebuild Script
# Author: Antigravity (Expert Fullstack Dev)
# Purpose: Ensures Swagger and MkDocs are perfectly synchronized with the code.
# ==============================================================================

set -e

# 1. Cleanup old artifacts and caches
echo "🧹 Cleaning old artifacts and caches..."
rm -rf site/
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
echo "✅ Cleanup complete."

# 2. Re-generate Swagger OpenAPI Schema
echo "🚀 Regenerating Swagger schema.yml..."
# Ensure we are in the project root
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

# Try to use .venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python manage.py spectacular --file schema.yml
echo "✅ Swagger schema updated."

# 3. Build MkDocs Site
echo "📚 Building MkDocs site..."
mkdocs build --clean
echo "✅ MkDocs site rebuilt."

echo "=============================================================================="
echo "🎉 SUCCESS: All documentation artifacts are now up-to-date."
echo "Acceptance Check:"
echo " - Swagger: schema.yml updated."
echo " - MkDocs: site/ directory refreshed."
echo "=============================================================================="
