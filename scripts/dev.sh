#!/bin/bash
set -e

echo "🔧 Запуск в режиме разработки..."

# Проверка .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Запустите setup.sh"
    exit 1
fi

# Проверка токена МойСклад
if grep -q "your_moysklad_token_here" .env; then
    echo "⚠️  Внимание: Не настроен MOYSKLAD_TOKEN в .env файле"
    echo "   Получите токен: https://app.moysklad.ru → Настройки → API"
fi

# Сборка и запуск сервисов
echo "🏗️  Сборка контейнеров..."
docker-compose build

echo "🚀 Запуск сервисов..."
docker-compose --profile development up -d

echo "⏳ Ожидание готовности сервисов..."
sleep 10

# Применение миграций
echo "📊 Применение миграций базы данных..."
docker-compose exec app-backend alembic upgrade head

echo ""
echo "✅ Система запущена!"
echo ""
echo "🌐 Доступные сервисы:"
echo "   Frontend:        http://localhost:3000"
echo "   Backend API:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/docs"
echo "   Adminer (DB):    http://localhost:8080"
echo "   Redis Commander: http://localhost:8081"
echo ""
echo "📋 Полезные команды:"
echo "   Просмотр логов:    docker-compose logs -f"
echo "   Остановка:         docker-compose down"
echo "   Перезапуск:        docker-compose restart"