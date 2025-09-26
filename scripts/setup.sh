#!/bin/bash

# Setup script for CRM MoySklad Integration

set -e

echo "🚀 Setting up CRM MoySklad Integration..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists."
fi

# Create backend .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file from template..."
    cp backend/env.example backend/.env
    echo "✅ backend/.env file created. Please edit it with your configuration."
else
    echo "✅ backend/.env file already exists."
fi

# Create frontend .env file if it doesn't exist
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend/.env file from template..."
    cp frontend/env.example frontend/.env
    echo "✅ frontend/.env file created. Please edit it with your configuration."
else
    echo "✅ frontend/.env file already exists."
fi

echo ""
echo "🔧 Next steps:"
echo "1. Edit .env files with your configuration"
echo "2. Get your MoySklad token from https://app.moysklad.ru/app/#settings/api"
echo "3. Add the token to backend/.env file"
echo "4. Run: docker-compose up --build"
echo ""
echo "⚠️  IMPORTANT: Never commit real tokens to the repository!"
echo ""
echo "✅ Setup complete!"
