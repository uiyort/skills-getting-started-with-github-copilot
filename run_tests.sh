#!/bin/bash
# Test runner script for the school activity management system

echo "Running FastAPI tests..."
echo "========================"

# Activate virtual environment and run tests
cd "$(dirname "$0")"
.venv/bin/python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "Test run complete!"
echo "HTML coverage report generated in htmlcov/index.html"