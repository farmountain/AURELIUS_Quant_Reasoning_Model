#!/bin/bash
# Integration Test Runner Script
# Runs the AURELIUS API integration test suite

set -e

echo "================================"
echo "AURELIUS Integration Test Suite"
echo "================================"
echo ""

# Check if API is running
echo "Checking API connectivity..."
if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "❌ API server is not running on http://127.0.0.1:8000"
    echo ""
    echo "Start the API with:"
    echo "  cd api"
    echo "  python -m uvicorn main:app --reload"
    exit 1
fi

echo "✅ API server is running"
echo ""

# Run Python test suite
echo "Running integration tests..."
python test_integration.py

echo ""
echo "Integration tests complete!"
