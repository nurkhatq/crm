# CRM МойСклад Integration

Полнофункциональная CRM система с интеграцией МойСклад для чтения и анализа данных. Система предоставляет веб-интерфейс для просмотра товаров, клиентов, документов и аналитики на основе данных из МойСклад.

## 🚀 Особенности

- **Read-only интеграция** с API МойСклад (только чтение данных)
- **Современный стек**: FastAPI + Next.js + PostgreSQL + Redis
- **Background синхронизация** с Celery
- **Аналитика и прогнозирование** продаж
- **Экспорт данных** в CSV
- **Docker Compose** для простого развертывания
- **Полное тестирование** и CI/CD
- **Безопасность**: JWT аутентификация, валидация токенов

## 📋 Требования

- Docker и Docker Compose
- Git
- Node.js 18+ (для разработки)
- Python 3.11+ (для разработки)

## 🛠 Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd crm
```

### 2. Настройка окружения

Скопируйте файл с переменными окружения:

```bash
cp env.example .env
```

Отредактируйте `.env` файл и укажите необходимые параметры:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=crm_dev
DATABASE_URL=postgresql://postgres:postgres@db:5432/crm_dev

# Redis
REDIS_URL=redis://redis:6379/0

# MoySklad API (ОБЯЗАТЕЛЬНО!)
MOYSKLAD_TOKEN=your_moysklad_token_here

# JWT Authentication
JWT_SECRET=replace_me_with_strong_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Sentry (опционально)
SENTRY_DSN=

# FastAPI Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Cache Settings
CACHE_TTL=300
SYNC_INTERVAL=3600
```

### 3. Получение токена МойСклад

⚠️ **ВАЖНО**: Никогда не коммитьте реальные токены в репозиторий!

1. Войдите в ваш аккаунт МойСклад
2. Перейдите в Настройки → API
3. Создайте новый токен доступа
4. Скопируйте токен и вставьте в `.env` файл

### 4. Запуск приложения

```bash
# Запуск всех сервисов
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build
```

### 5. Применение миграций

```bash
# Войти в контейнер backend
docker-compose exec app-backend bash

# Применить миграции
alembic upgrade head
```

### 6. Доступ к приложению

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Adminer (DB)**: http://localhost:8080 (если добавлен в docker-compose)

## 📁 Структура проекта

```
crm/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── connectors/     # MoySklad connector
│   │   ├── core/           # Configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── components/         # React components
│   ├── pages/             # Next.js pages
│   ├── lib/               # API client
│   ├── styles/            # CSS styles
│   └── package.json
├── docker-compose.yml      # Docker services
├── .github/workflows/      # CI/CD
└── README.md
```

## 🔧 Разработка

### Backend разработка

```bash
cd backend

# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск Celery worker
celery -A app.celery worker --loglevel=info

# Запуск тестов
pytest tests/ -v

# Линтинг
black .
isort .
ruff check .
mypy app/
```

### Frontend разработка

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск в режиме разработки
npm run dev

# Запуск тестов
npm test

# Линтинг
npm run lint
```

### Создание миграций

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

## 📊 API Endpoints

### Основные endpoints

- `GET /api/v1/products/` - Список товаров
- `GET /api/v1/products/{id}` - Детали товара
- `GET /api/v1/customers/` - Список клиентов
- `GET /api/v1/documents/` - Список документов
- `GET /api/v1/analytics/kpi` - KPI метрики
- `GET /api/v1/analytics/products/top` - Топ товаров
- `POST /api/v1/connectors/moysklad/sync` - Запуск синхронизации

### Экспорт данных

- `GET /api/v1/products/export/csv` - Экспорт товаров в CSV
- `GET /api/v1/customers/export/csv` - Экспорт клиентов в CSV
- `GET /api/v1/documents/export/csv` - Экспорт документов в CSV

## 🔄 Синхронизация данных

Система поддерживает несколько типов синхронизации:

- **Полная синхронизация**: `POST /api/v1/connectors/moysklad/sync` с `{"sync_type": "full"}`
- **Товары**: `{"sync_type": "products"}`
- **Клиенты**: `{"sync_type": "customers"}`
- **Документы**: `{"sync_type": "documents"}`
- **Остатки**: `{"sync_type": "stock"}`

Синхронизация выполняется в фоновом режиме через Celery.

## 🧪 Тестирование

### Backend тесты

```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend тесты

```bash
cd frontend
npm test
```

### E2E тесты

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск тестов
docker-compose exec app-backend pytest tests/test_e2e.py
```

## 🚀 Развертывание в продакшн

### 1. Настройка переменных окружения

Создайте `.env.production` с продакшн настройками:

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://user:password@prod-db:5432/crm_prod
REDIS_URL=redis://prod-redis:6379/0
MOYSKLAD_TOKEN=your_production_token
JWT_SECRET=your_strong_production_secret
```

### 2. Использование секретов

В продакшне используйте секретные хранилища (AWS Secrets Manager, Azure Key Vault, etc.) вместо `.env` файлов.

### 3. Docker Compose для продакшна

Создайте `docker-compose.prod.yml` с продакшн конфигурацией.

## 🔒 Безопасность

### Токены и секреты

- ❌ **НИКОГДА** не коммитьте реальные токены в репозиторий
- ✅ Используйте `.env` файлы для локальной разработки
- ✅ Используйте секретные хранилища в продакшне
- ✅ Регулярно ротируйте токены

### Если токен был скомпрометирован

1. Немедленно отзовите токен в МойСклад
2. Создайте новый токен
3. Обновите конфигурацию
4. Проверьте логи на предмет несанкционированного доступа

## 📈 Мониторинг

### Логи

Логи доступны через Docker:

```bash
# Все сервисы
docker-compose logs

# Конкретный сервис
docker-compose logs app-backend
docker-compose logs worker
```

### Метрики

- Prometheus метрики: http://localhost:8000/metrics
- Health check: http://localhost:8000/health

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

### Требования к PR

- ✅ Все тесты проходят
- ✅ Линтинг проходит без ошибок
- ✅ Покрытие тестами не уменьшилось
- ✅ Документация обновлена
- ✅ Нет реальных токенов в коде

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

Если у вас возникли проблемы:

1. Проверьте [Issues](https://github.com/your-repo/issues)
2. Создайте новый Issue с подробным описанием
3. Приложите логи и конфигурацию (без токенов!)

## 🔄 Changelog

### v1.0.0
- Первоначальный релиз
- Интеграция с МойСклад API
- Веб-интерфейс на Next.js
- Аналитика и прогнозирование
- Экспорт данных в CSV
- Полное тестирование и CI/CD

---

**⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ О БЕЗОПАСНОСТИ**

Этот проект предназначен для чтения данных из МойСклад. Никогда не включайте реальные токены доступа в код или не загружайте их в публичные репозитории. Всегда используйте переменные окружения и секретные хранилища для хранения чувствительной информации.
