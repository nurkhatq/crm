#!/bin/bash
set -e

echo "🚀 Настройка CRM МойСклад системы..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и Docker Compose"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Создание .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "✅ Создан .env файл. Настройте MOYSKLAD_TOKEN!"
else
    echo "⚠️  .env файл уже существует"
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p backend/backups
mkdir -p frontend/.next

# Установка прав доступа
chmod +x scripts/*.sh

echo "🎉 Первоначальная настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте MOYSKLAD_TOKEN в файле .env"
echo "2. Запустите: ./scripts/dev.sh"
echo "3. Проверьте: http://localhost:3000"
echo ""
echo "🔗 Полезные ссылки:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Adminer (DB): http://localhost:8080"