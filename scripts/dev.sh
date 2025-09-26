#!/bin/bash

# Development script for CRM MoySklad Integration

set -e

echo "🔧 Starting development environment..."

# Check if .env files exist
if [ ! -f .env ] || [ ! -f backend/.env ] || [ ! -f frontend/.env ]; then
    echo "❌ Environment files not found. Please run ./scripts/setup.sh first."
    exit 1
fi

# Check if MoySklad token is configured
if grep -q "your_moysklad_token_here" backend/.env; then
    echo "⚠️  WARNING: MoySklad token not configured in backend/.env"
    echo "   Please add your token to enable data synchronization."
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo "✅ Development environment started!"
echo ""
echo "🌐 Services available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Run migrations: docker-compose exec app-backend alembic upgrade head"
echo ""
echo "🔄 To sync data from MoySklad:"
echo "   curl -X POST http://localhost:8000/api/v1/connectors/moysklad/sync \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"sync_type\": \"full\", \"force\": false}'"
