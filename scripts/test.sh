#!/bin/bash

# Test script for CRM MoySklad Integration

set -e

echo "🧪 Running tests..."

# Backend tests
echo "🔧 Running backend tests..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running backend tests..."
pytest tests/ -v --cov=app --cov-report=html

# Deactivate virtual environment
deactivate

cd ..

# Frontend tests
echo "🔧 Running frontend tests..."
cd frontend

# Install dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Run tests
echo "🧪 Running frontend tests..."
npm test -- --coverage

cd ..

echo "✅ All tests completed!"
echo ""
echo "📊 Coverage reports:"
echo "   Backend: backend/htmlcov/index.html"
echo "   Frontend: frontend/coverage/lcov-report/index.html"
