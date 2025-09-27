# scripts/prod.sh - Скрипт для продакшна

#!/bin/bash
set -e

echo "🏭 Запуск в продакшн режиме..."

# Проверки для продакшна
if [ "$APP_ENV" != "production" ]; then
    echo "⚠️  Предупреждение: APP_ENV не установлен в 'production'"
fi

if grep -q "your_moysklad_token_here" .env; then
    echo "❌ Ошибка: Токен МойСклад не настроен!"
    exit 1
fi

if grep -q "your-super-secret-jwt-key" .env; then
    echo "❌ Ошибка: JWT_SECRET не изменен!"
    exit 1
fi

# Сборка для продакшна
echo "🏗️  Сборка продакшн образов..."
docker-compose -f docker-compose.yml --profile production build --no-cache

echo "🚀 Запуск продакшн сервисов..."
docker-compose -f docker-compose.yml --profile production up -d

echo "📊 Применение миграций..."
docker-compose exec app-backend alembic upgrade head

echo ""
echo "✅ Продакшн система запущена!"
echo ""
echo "🔒 Безопасность:"
echo "   - Используйте HTTPS в продакшне"
echo "   - Настройте файрволл"
echo "   - Регулярно обновляйте токены"