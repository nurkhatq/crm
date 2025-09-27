#!/bin/bash
set -e

BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_BACKUP_FILE="crm_backup_${TIMESTAMP}.sql"

echo "💾 Создание резервной копии..."

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных
echo "📊 Бэкап базы данных..."
docker-compose exec -T db pg_dump -U postgres crm_dev > "${BACKUP_DIR}/${DB_BACKUP_FILE}"

# Сжатие бэкапа
echo "🗜️  Сжатие архива..."
gzip "${BACKUP_DIR}/${DB_BACKUP_FILE}"

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "✅ Резервная копия создана: ${DB_BACKUP_FILE}.gz"