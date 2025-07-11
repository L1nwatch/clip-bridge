#!/bin/bash

# CI Validation Script
# Tests both Python and React components locally before pushing

set -e  # Exit on any error

echo "🚀 Starting CI Validation..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

echo ""
echo "📦 Installing dependencies..."
echo "------------------------------"

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm ci

# Check Python virtual environment
if [ ! -d "utils/.venv" ]; then
    echo "❌ Error: Python virtual environment not found at utils/.venv"
    echo "Please run: cd utils && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "🐍 Running Python Tests..."
echo "---------------------------"

# Run Python tests
npm run test:python

echo ""
echo "⚛️ Running React Tests..."
echo "--------------------------"

# Run React tests
npm run test:coverage

echo ""
echo "🧹 Running Linting..."
echo "---------------------"

# Python linting
echo "Checking Python code formatting..."
cd utils
source .venv/bin/activate
black --check *.py
flake8 *.py --count --select=E9,F63,F7,F82 --show-source --statistics
cd ..

# JavaScript linting
echo "Checking JavaScript code..."
npm run lint

echo ""
echo "📦 Testing Build..."
echo "-------------------"

# Test build
npm run build

echo ""
echo "✅ All validations passed!"
echo "=========================="
echo ""
echo "🎉 Your code is ready for CI/CD!"
echo ""
echo "Summary:"
echo "- ✅ Python tests: PASSED"
echo "- ✅ React tests: PASSED" 
echo "- ✅ Code linting: PASSED"
echo "- ✅ Build: PASSED"
echo ""
echo "You can now safely push your changes. 🚀"
