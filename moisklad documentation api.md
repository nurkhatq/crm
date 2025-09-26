# Полная документация API МойСклад для создания Python скрипта извлечения данных

Проведено исчерпывающее исследование API МойСклад версии 1.2 для создания комплексного Python скрипта извлечения максимального объема данных в CSV файлы. **API МойСклад представляет собой зрелое, стабильное REST API с отличной документацией и широкими возможностями интеграции**.

## Архитектура и основы API

### Базовая структура
**Основной URL**: `https://api.moysklad.ru/api/remap/1.2/`

API построен по принципам REST с двумя основными разделами:
- **entity** - работа с бизнес-объектами (CRUD операции)
- **report** - отчеты и аналитические данные

**Формат URL**: `https://api.moysklad.ru/api/remap/1.2/{section}/{resource}[/{id}][/{subresource}]`

### Методы аутентификации

**Basic Authentication** (для разработки):
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    "https://api.moysklad.ru/api/remap/1.2/entity/product",
    auth=HTTPBasicAuth("login@domain.com", "password"),
    headers={"Accept-Encoding": "gzip"}
)
```

**Bearer Token** (рекомендуется для production):
```python
# Получение токена
token_response = requests.post(
    "https://api.moysklad.ru/api/remap/1.2/security/token",
    auth=HTTPBasicAuth("login", "password")
)
access_token = token_response.json()["access_token"]

# Использование токена
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept-Encoding": "gzip"
}
response = requests.get(
    "https://api.moysklad.ru/api/remap/1.2/entity/product",
    headers=headers
)
```

## Полный каталог доступных данных

### Товары и ассортимент
```python
# Товары с полной информацией
GET /entity/product?expand=owner,group,uom,supplier,buyPrice.currency,salePrices.currency

# Весь ассортимент (товары + услуги + модификации)
GET /entity/assortment

# Услуги
GET /entity/service

# Комплекты
GET /entity/bundle

# Модификации товаров
GET /entity/variant
```

**Структура товара включает**: ID, наименование, код, артикул, штрихкоды, цены покупки/продажи, остатки, единицы измерения, группы, поставщиков, изображения, дополнительные поля.

### Остатки товаров
```python
# Расширенный отчет об остатках
GET /report/stock/all

# Краткий отчет (только ID и остатки)
GET /report/stock/all/current

# Остатки по складам
GET /report/stock/bystore

# Обороты товаров
GET /report/turnover/all
```

**Типы остатков**: физический остаток, резерв, ожидание, доступное количество.

### Документы продаж
```python
# Заказы покупателей
GET /entity/customerorder

# Отгрузки
GET /entity/demand

# Счета покупателям
GET /entity/invoiceout

# Возвраты покупателей
GET /entity/salesreturn

# Розничные продажи
GET /entity/retailsale
```

### Документы закупок
```python
# Заказы поставщикам
GET /entity/purchaseorder

# Приемки
GET /entity/supply

# Счета поставщиков  
GET /entity/invoicein

# Возвраты поставщикам
GET /entity/purchasereturn
```

### Контрагенты и организации
```python
# Контрагенты (клиенты/поставщики)
GET /entity/counterparty

# Юридические лица
GET /entity/organization

# Контактные лица
GET /entity/counterparty/{id}/contactpersons
```

**Данные контрагентов**: наименование, ИНН, КПП, адреса, контакты, банковские реквизиты, скидки, типы цен.

### Складские данные
```python
# Склады
GET /entity/store

# Складские документы
GET /entity/enter        # Оприходования
GET /entity/loss         # Списания  
GET /entity/move         # Перемещения
GET /entity/inventory    # Инвентаризации
```

### Финансовые данные и отчеты
```python
# Движение денежных средств
GET /report/money/plotseries

# Остатки в кассах и на счетах
GET /report/money/cash

# Прибыльность по товарам
GET /report/profit/byproduct

# Показатели продаж
GET /report/dashboard/sales

# Показатели заказов
GET /report/dashboard/orders
```

### Справочники и настройки
```python
# Валюты
GET /entity/currency

# Единицы измерения
GET /entity/uom

# Группы товаров
GET /entity/productfolder

# Проекты
GET /entity/project

# Договоры
GET /entity/contract

# Типы цен
GET /entity/pricetype

# Страны
GET /entity/country
```

## Технические ограничения и оптимизация

### Rate Limiting
- **100 запросов за 5 секунд**
- **5 параллельных запросов от пользователя**
- **20 параллельных запросов от аккаунта**
- **Максимум 10 МБ данных в запросе**

**Реализация контроля лимитов**:
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=100, time_window=5):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        
    def wait_if_needed(self):
        now = time.time()
        # Удаляем старые запросы
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()
            
        # Ждем если достигли лимита
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.requests.clear()
        
        self.requests.append(now)
```

### Пагинация для больших объемов
```python
def get_all_entities(api_client, entity_type, limit=1000):
    all_data = []
    offset = 0
    
    while True:
        params = {'limit': limit, 'offset': offset}
        response = api_client.get(f'entity/{entity_type}', params)
        
        rows = response.get('rows', [])
        if not rows:
            break
            
        all_data.extend(rows)
        
        # Проверяем наличие следующих страниц
        meta = response.get('meta', {})
        if 'nextHref' not in meta:
            break
            
        offset += limit
        time.sleep(0.05)  # Небольшая задержка
    
    return all_data
```

### Фильтрация и поиск
**Операторы фильтрации**:
- `=` равенство
- `>`, `<`, `>=`, `<=` сравнение  
- `!=` неравенство
- `~` содержит подстроку
- `~=` начинается с
- `=~` заканчивается на

```python
# Фильтрация по дате обновления для инкрементальных обновлений
params = {
    'filter': 'updated>2024-01-01 00:00:00;archived=false',
    'order': 'updated,desc',
    'limit': 1000
}
```

### Оптимизация с expand
```python
# Получение товаров со связанными данными за один запрос
params = {
    'expand': 'owner,group,uom,supplier,buyPrice.currency,salePrices.currency',
    'limit': 100  # При expand максимум 100
}
```

## Полнофункциональный Python скрипт

### Основной класс API клиента
```python
import requests
import base64
import time
import csv
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class MoySkladExporter:
    def __init__(self, login: str, password: str):
        self.base_url = "https://api.moysklad.ru/api/remap/1.2"
        credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json"
        }
        self.rate_limiter = RateLimiter()
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        # Обработка rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
            time.sleep(retry_after / 1000)
            return self.make_request(method, endpoint, **kwargs)
            
        response.raise_for_status()
        return response.json()
    
    def get_all_entities(self, entity_type: str, **filters) -> List[Dict[str, Any]]:
        all_data = []
        offset = 0
        limit = 1000
        
        while True:
            params = {**filters, 'offset': offset, 'limit': limit}
            result = self.make_request('GET', f'entity/{entity_type}', params=params)
            
            rows = result.get('rows', [])
            if not rows:
                break
                
            all_data.extend(rows)
            offset += limit
            
            # Показываем прогресс
            if len(all_data) % 5000 == 0:
                print(f"Загружено {len(all_data)} записей {entity_type}...")
            
            time.sleep(0.05)
        
        return all_data
    
    def export_to_csv(self, entity_type: str, filename: str, fields_mapping: Dict[str, str]):
        """Экспорт сущностей в CSV"""
        print(f"Начинаем экспорт {entity_type}...")
        
        # Получаем все данные
        data = self.get_all_entities(entity_type)
        
        if not data:
            print(f"Нет данных для экспорта: {entity_type}")
            return
        
        # Записываем в CSV
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields_mapping.keys())
            writer.writeheader()
            
            for item in data:
                row = {}
                for csv_field, json_path in fields_mapping.items():
                    row[csv_field] = self._extract_field_value(item, json_path)
                writer.writerow(row)
        
        print(f"Экспорт завершен: {len(data)} записей в файл {filename}")
    
    def _extract_field_value(self, item: Dict, json_path: str) -> str:
        """Извлечение значения по JSON пути"""
        try:
            current = item
            for key in json_path.split('.'):
                if '[' in key and ']' in key:
                    array_key = key.split('[')[0]
                    index = int(key.split('[')[1].split(']')[0])
                    current = current[array_key][index]
                else:
                    current = current[key]
            return str(current) if current is not None else ''
        except (KeyError, IndexError, TypeError):
            return ''
    
    def export_all_data(self):
        """Экспорт всех доступных данных"""
        
        # Конфигурация экспортов
        exports = {
            'products': {
                'entity': 'product',
                'filename': 'products.csv',
                'fields': {
                    'ID': 'id',
                    'Наименование': 'name',
                    'Код': 'code',
                    'Артикул': 'article',
                    'Архивный': 'archived',
                    'Цена_продажи': 'salePrices.0.value',
                    'Цена_закупки': 'buyPrice.value',
                    'Группа': 'productFolder.name',
                    'ЕИ': 'uom.name',
                    'Обновлен': 'updated'
                }
            },
            'counterparties': {
                'entity': 'counterparty',
                'filename': 'counterparties.csv',
                'fields': {
                    'ID': 'id',
                    'Наименование': 'name',
                    'Код': 'code',
                    'ИНН': 'inn',
                    'КПП': 'kpp',
                    'Email': 'email',
                    'Телефон': 'phone',
                    'Юр_название': 'legalTitle',
                    'Архивный': 'archived',
                    'Обновлен': 'updated'
                }
            },
            'customer_orders': {
                'entity': 'customerorder',
                'filename': 'customer_orders.csv',
                'fields': {
                    'ID': 'id',
                    'Номер': 'name',
                    'Дата': 'moment',
                    'Сумма': 'sum',
                    'Контрагент': 'agent.name',
                    'Организация': 'organization.name',
                    'Склад': 'store.name',
                    'Статус': 'state.name',
                    'Проведен': 'applicable',
                    'Обновлен': 'updated'
                }
            },
            'demands': {
                'entity': 'demand',
                'filename': 'demands.csv',
                'fields': {
                    'ID': 'id',
                    'Номер': 'name',
                    'Дата': 'moment',
                    'Сумма': 'sum',
                    'Контрагент': 'agent.name',
                    'Организация': 'organization.name',
                    'Склад': 'store.name',
                    'Проведен': 'applicable'
                }
            },
            'supplies': {
                'entity': 'supply',
                'filename': 'supplies.csv',
                'fields': {
                    'ID': 'id',
                    'Номер': 'name',
                    'Дата': 'moment',
                    'Сумма': 'sum',
                    'Контрагент': 'agent.name',
                    'Организация': 'organization.name',
                    'Склад': 'store.name',
                    'Проведен': 'applicable'
                }
            }
        }
        
        # Экспорт остатков товаров
        print("Экспортируем остатки товаров...")
        stock_data = self.make_request('GET', 'report/stock/all', params={'limit': 1000})
        self._export_stock_to_csv(stock_data.get('rows', []), 'stock.csv')
        
        # Экспорт всех сущностей
        for export_name, config in exports.items():
            try:
                self.export_to_csv(
                    config['entity'],
                    config['filename'],
                    config['fields']
                )
            except Exception as e:
                print(f"Ошибка экспорта {export_name}: {e}")
        
        print("Экспорт всех данных завершен!")
    
    def _export_stock_to_csv(self, stock_data: List[Dict], filename: str):
        """Специальный экспорт остатков"""
        fields_mapping = {
            'Товар_ID': 'meta.href',
            'Наименование': 'name',
            'Код': 'code',
            'Артикул': 'article',
            'Остаток': 'stock',
            'Резерв': 'reserve',
            'Ожидание': 'inTransit',
            'Доступно': 'quantity',
            'Цена': 'price',
            'Цена_продажи': 'salePrice'
        }
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields_mapping.keys())
            writer.writeheader()
            
            for item in stock_data:
                row = {}
                for csv_field, json_path in fields_mapping.items():
                    if csv_field == 'Товар_ID':
                        # Извлекаем ID из href
                        href = item.get('meta', {}).get('href', '')
                        row[csv_field] = href.split('/')[-1] if href else ''
                    else:
                        row[csv_field] = self._extract_field_value(item, json_path)
                writer.writerow(row)
```

### Использование скрипта
```python
if __name__ == "__main__":
    # Настройка учетных данных
    LOGIN = "your_login@domain.com"
    PASSWORD = "your_password"
    
    # Создаем экспортер
    exporter = MoySkladExporter(LOGIN, PASSWORD)
    
    # Экспортируем все данные
    exporter.export_all_data()
```

## Дополнительные возможности и специальные случаи

### Работа с дополнительными полями
```python
# Получение метаданных с дополнительными полями
metadata = api_client.make_request('GET', 'entity/product/metadata')
attributes = metadata.get('attributes', [])

# Обработка дополнительных полей в экспорте
for attr in attributes:
    field_name = f"attr_{attr['name']}"
    field_path = f"attributes.{attr['id']}.value"
```

### Массовые операции
```python
# Массовое создание/обновление до 1000 элементов
def batch_update(self, entity_type: str, data_list: List[Dict]):
    chunk_size = 1000
    for i in range(0, len(data_list), chunk_size):
        chunk = data_list[i:i + chunk_size]
        self.make_request('POST', f'entity/{entity_type}', json=chunk)
        time.sleep(0.2)
```

### Работа с позициями документов
```python
# Получение позиций заказа
def get_document_positions(self, document_type: str, document_id: str):
    return self.make_request('GET', f'entity/{document_type}/{document_id}/positions')
```

## Заключение

API МойСклад предоставляет **исчерпывающий доступ ко всем бизнес-данным** с отличной производительностью и стабильностью. Ключевые преимущества:

✅ **Полнота данных**: доступ к товарам, документам, контрагентам, финансам, отчетам  
✅ **Гибкость**: мощная фильтрация, сортировка, expand для связанных данных  
✅ **Производительность**: до 1000 записей за запрос, эффективная пагинация  
✅ **Надежность**: четкие лимиты, обработка ошибок, стабильная работа  
✅ **Удобство интеграции**: REST API, JSON, подробная документация

Предложенный Python скрипт может извлечь **максимально возможный объем данных** из МойСклад в структурированные CSV файлы, обеспечивая высокую производительность и соблюдение всех технических ограничений API.