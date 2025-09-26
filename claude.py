#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moysklad_export.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Контроль лимитов запросов к API"""
    
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
                logger.warning(f"Rate limit достигнут. Ожидаем {sleep_time:.2f} секунд")
                time.sleep(sleep_time)
                self.requests.clear()
        
        self.requests.append(now)

class MoySkladFullExporter:
    """Полный экспортер всех данных МойСклад"""
    
    def __init__(self, token: str, output_dir: str = "moysklad_export"):
        self.token = token
        self.base_url = "https://api.moysklad.ru/api/remap/1.2"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "User-Agent": "MoySkladFullExporter/1.0"
        }
        self.rate_limiter = RateLimiter(max_requests=95, time_window=5)
        self.output_dir = output_dir
        self.stats = {}
        
        # Создаем директорию для экспорта
        os.makedirs(output_dir, exist_ok=True)
        
        # Проверяем подключение
        self._test_connection()
    
    def _test_connection(self):
        """Тестирование подключения к API"""
        try:
            response = self.make_request('GET', 'context/employee')
            logger.info(f"Подключение успешно. Пользователь: {response.get('name', 'Неизвестен')}")
        except Exception as e:
            logger.error(f"Ошибка подключения к API: {e}")
            raise
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение запроса к API с обработкой ошибок и rate limiting"""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            
            # Обработка rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                time.sleep(retry_after / 1000)
                return self.make_request(method, endpoint, **kwargs)
            
            # Проверка статуса ответа
            if response.status_code == 401:
                logger.error("Ошибка аутентификации. Проверьте токен")
                raise Exception("Неверный токен")
            
            response.raise_for_status()
            
            # Парсинг JSON
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return {"content": response.text}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к {url}: {e}")
            raise
    
    def get_all_entities(self, entity_type: str, expand: str = None, filters: str = None) -> List[Dict[str, Any]]:
        """Получение всех сущностей с пагинацией"""
        all_data = []
        offset = 0
        limit = 1000
        
        # Уменьшаем лимит при использовании expand
        if expand:
            limit = 100
            
        logger.info(f"Начинаем загрузку {entity_type}...")
        
        while True:
            params = {'offset': offset, 'limit': limit}
            
            if expand:
                params['expand'] = expand
            if filters:
                params['filter'] = filters
                
            try:
                result = self.make_request('GET', f'entity/{entity_type}', params=params)
                
                rows = result.get('rows', [])
                if not rows:
                    break
                
                all_data.extend(rows)
                offset += limit
                
                # Показываем прогресс каждые 1000 записей
                if len(all_data) % 1000 == 0:
                    logger.info(f"Загружено {len(all_data)} записей {entity_type}...")
                
                # Небольшая пауза между запросами
                time.sleep(0.02)
                
                # Проверяем наличие следующих страниц
                meta = result.get('meta', {})
                if offset >= meta.get('size', 0):
                    break
                    
            except Exception as e:
                logger.error(f"Ошибка получения {entity_type} на offset {offset}: {e}")
                break
        
        logger.info(f"Загружено всего {len(all_data)} записей {entity_type}")
        self.stats[entity_type] = len(all_data)
        return all_data
    
    def get_report_data(self, report_type: str, params: dict = None) -> List[Dict[str, Any]]:
        """Получение данных отчетов"""
        if params is None:
            params = {}
        
        logger.info(f"Загружаем отчет {report_type}...")
        
        try:
            if 'limit' not in params:
                params['limit'] = 1000
                
            result = self.make_request('GET', f'report/{report_type}', params=params)
            
            if 'rows' in result:
                data = result['rows']
            elif isinstance(result, list):
                data = result
            else:
                data = [result]
            
            logger.info(f"Загружен отчет {report_type}: {len(data)} записей")
            self.stats[f'report_{report_type}'] = len(data)
            return data
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета {report_type}: {e}")
            return []
    
    def safe_get(self, data: Dict, path: str, default: str = '') -> str:
        """Безопасное извлечение значения по пути"""
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if '[' in key and ']' in key:
                    # Обработка массивов: key[0]
                    array_key = key.split('[')[0]
                    index = int(key.split('[')[1].split(']')[0])
                    current = current[array_key][index]
                else:
                    current = current[key]
            
            # Конвертация в строку
            if isinstance(current, (dict, list)):
                return json.dumps(current, ensure_ascii=False)
            elif current is None:
                return default
            else:
                return str(current)
                
        except (KeyError, IndexError, TypeError, ValueError):
            return default
    
    def export_to_csv(self, data: List[Dict], filename: str, fields_mapping: Dict[str, str]):
        """Экспорт данных в CSV файл"""
        if not data:
            logger.warning(f"Нет данных для экспорта в {filename}")
            return
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields_mapping.keys())
                writer.writeheader()
                
                for item in data:
                    row = {}
                    for csv_field, json_path in fields_mapping.items():
                        row[csv_field] = self.safe_get(item, json_path)
                    writer.writerow(row)
            
            logger.info(f"Экспорт завершен: {len(data)} записей в {filename}")
            
        except Exception as e:
            logger.error(f"Ошибка записи в {filename}: {e}")
    
    def export_products(self):
        """Экспорт товаров"""
        logger.info("=== ЭКСПОРТ ТОВАРОВ ===")
        
        # Товары с расширенной информацией
        expand = "owner,group,uom,supplier,buyPrice.currency,salePrices.currency,images"
        products = self.get_all_entities('product', expand=expand)
        
        fields = {
            'ID': 'id',
            'Наименование': 'name',
            'Код': 'code',
            'Артикул': 'article',
            'Описание': 'description',
            'Архивный': 'archived',
            'Весовой': 'weighed',
            'НДС': 'vat',
            'Цена_покупки': 'buyPrice.value',
            'Валюта_покупки': 'buyPrice.currency.name',
            'Цена_продажи_1': 'salePrices.0.value',
            'Цена_продажи_2': 'salePrices.1.value', 
            'Группа_товаров': 'productFolder.name',
            'Единица_измерения': 'uom.name',
            'Поставщик': 'supplier.name',
            'Минимальный_остаток': 'minimumBalance',
            'Штрихкоды': 'barcodes',
            'Страна': 'country.name',
            'Создан': 'created',
            'Обновлен': 'updated'
        }
        
        self.export_to_csv(products, 'products.csv', fields)
        
        # Экспорт услуг
        services = self.get_all_entities('service')
        self.export_to_csv(services, 'services.csv', fields)
        
        # Экспорт комплектов
        bundles = self.get_all_entities('bundle')
        self.export_to_csv(bundles, 'bundles.csv', fields)
        
        # Экспорт модификаций
        variants = self.get_all_entities('variant')
        variant_fields = {**fields, 'Основной_товар': 'product.name', 'Характеристики': 'characteristics'}
        self.export_to_csv(variants, 'variants.csv', variant_fields)
    
    def export_stock_reports(self):
        """Экспорт отчетов по остаткам"""
        logger.info("=== ЭКСПОРТ ОСТАТКОВ ===")
        
        # Остатки товаров
        stock_data = self.get_report_data('stock/all')
        stock_fields = {
            'Товар_ID': 'meta.href',
            'Наименование': 'name',
            'Код': 'code', 
            'Артикул': 'article',
            'Остаток': 'stock',
            'Резерв': 'reserve',
            'Ожидание': 'inTransit',
            'Доступно': 'quantity',
            'Себестоимость': 'price',
            'Цена_продажи': 'salePrice',
            'Склад': 'stockByStore'
        }
        self.export_to_csv(stock_data, 'stock_all.csv', stock_fields)
        
        # Краткие остатки
        stock_current = self.get_report_data('stock/all/current')
        current_fields = {
            'Товар_ID': 'meta.href',
            'Остаток': 'stock',
            'Резерв': 'reserve', 
            'Ожидание': 'inTransit',
            'Доступно': 'quantity'
        }
        self.export_to_csv(stock_current, 'stock_current.csv', current_fields)
        
        # Обороты товаров
        turnover_data = self.get_report_data('turnover/all')
        turnover_fields = {
            'Товар_ID': 'meta.href',
            'Наименование': 'name',
            'Остаток_начальный': 'stockAtPeriodStart',
            'Приход': 'income',
            'Расход': 'outcome',
            'Остаток_конечный': 'stockAtPeriodEnd'
        }
        self.export_to_csv(turnover_data, 'turnover.csv', turnover_fields)
    
    def export_counterparties(self):
        """Экспорт контрагентов"""
        logger.info("=== ЭКСПОРТ КОНТРАГЕНТОВ ===")
        
        expand = "owner,group,state,tags"
        counterparties = self.get_all_entities('counterparty', expand=expand)
        
        fields = {
            'ID': 'id',
            'Наименование': 'name',
            'Код': 'code',
            'Внешний_код': 'externalCode',
            'Архивный': 'archived',
            'ИНН': 'inn',
            'КПП': 'kpp',
            'ОГРН': 'ogrn',
            'ОКПО': 'okpo',
            'Email': 'email',
            'Телефон': 'phone',
            'Факс': 'fax',
            'Юридическое_название': 'legalTitle',
            'Юридический_адрес': 'legalAddress',
            'Фактический_адрес': 'actualAddress',
            'Тип': 'companyType',
            'Владелец': 'owner.name',
            'Группа': 'group.name',
            'Скидка': 'discountPercentage',
            'Теги': 'tags',
            'Примечание': 'note',
            'Создан': 'created',
            'Обновлен': 'updated'
        }
        
        self.export_to_csv(counterparties, 'counterparties.csv', fields)
    
    def export_organizations(self):
        """Экспорт организаций"""
        logger.info("=== ЭКСПОРТ ОРГАНИЗАЦИЙ ===")
        
        organizations = self.get_all_entities('organization')
        
        fields = {
            'ID': 'id',
            'Наименование': 'name',
            'Код': 'code',
            'Архивный': 'archived',
            'ИНН': 'inn',
            'КПП': 'kpp',
            'ОГРН': 'ogrn',
            'ОКПО': 'okpo',
            'Email': 'email',
            'Телефон': 'phone',
            'Юридическое_название': 'legalTitle',
            'Юридический_адрес': 'legalAddress',
            'Фактический_адрес': 'actualAddress',
            'Главный_бухгалтер': 'chiefAccountant',
            'Директор': 'director',
            'Создан': 'created',
            'Обновлен': 'updated'
        }
        
        self.export_to_csv(organizations, 'organizations.csv', fields)
    
    def export_documents(self):
        """Экспорт всех документов"""
        logger.info("=== ЭКСПОРТ ДОКУМЕНТОВ ===")
        
        document_types = [
            'customerorder',    # Заказы покупателей
            'demand',          # Отгрузки
            'supply',          # Приемки
            'invoiceout',      # Счета покупателям
            'invoicein',       # Счета поставщиков
            'purchaseorder',   # Заказы поставщикам
            'salesreturn',     # Возвраты покупателей
            'purchasereturn',  # Возвраты поставщикам
            'enter',           # Оприходования
            'loss',            # Списания
            'move',            # Перемещения
            'inventory',       # Инвентаризации
            'retaildemand',    # Розничные продажи
            'retailsalesreturn' # Возвраты розничных продаж
        ]
        
        common_fields = {
            'ID': 'id',
            'Номер': 'name',
            'Дата': 'moment',
            'Сумма': 'sum',
            'Контрагент': 'agent.name',
            'Организация': 'organization.name',
            'Склад': 'store.name',
            'Проект': 'project.name',
            'Статус': 'state.name',
            'Проведен': 'applicable',
            'Напечатан': 'printed',
            'Опубликован': 'published',
            'НДС': 'vatSum',
            'Комментарий': 'description',
            'Владелец': 'owner.name',
            'Создан': 'created',
            'Обновлен': 'updated'
        }
        
        for doc_type in document_types:
            try:
                documents = self.get_all_entities(doc_type)
                filename = f'{doc_type}.csv'
                self.export_to_csv(documents, filename, common_fields)
            except Exception as e:
                logger.error(f"Ошибка экспорта документов {doc_type}: {e}")
    
    def export_dictionaries(self):
        """Экспорт справочников"""
        logger.info("=== ЭКСПОРТ СПРАВОЧНИКОВ ===")
        
        dictionaries = [
            ('currency', 'currencies.csv', {
                'ID': 'id', 'Код': 'code', 'Наименование': 'name', 'Полное_имя': 'fullName',
                'Курс': 'rate', 'Косвенная': 'indirect', 'Архивная': 'archived'
            }),
            ('uom', 'units.csv', {
                'ID': 'id', 'Код': 'code', 'Наименование': 'name', 'Описание': 'description',
                'Внешний_код': 'externalCode'
            }),
            ('country', 'countries.csv', {
                'ID': 'id', 'Код': 'code', 'Наименование': 'name', 'Описание': 'description',
                'Внешний_код': 'externalCode'
            }),
            ('productfolder', 'product_folders.csv', {
                'ID': 'id', 'Наименование': 'name', 'Код': 'code', 'Внешний_код': 'externalCode',
                'Архивная': 'archived', 'Родительская_группа': 'productFolder.name'
            }),
            ('project', 'projects.csv', {
                'ID': 'id', 'Наименование': 'name', 'Код': 'code', 'Описание': 'description',
                'Архивный': 'archived'
            }),
            ('contract', 'contracts.csv', {
                'ID': 'id', 'Наименование': 'name', 'Код': 'code', 'Внешний_код': 'externalCode',
                'Архивный': 'archived', 'Контрагент': 'agent.name', 'Организация': 'ownAgent.name'
            }),
            ('store', 'stores.csv', {
                'ID': 'id', 'Наименование': 'name', 'Код': 'code', 'Внешний_код': 'externalCode',
                'Архивный': 'archived', 'Адрес': 'address', 'Родительский_склад': 'parent.name'
            }),
            ('pricetype', 'price_types.csv', {
                'ID': 'id', 'Наименование': 'name', 'Внешний_код': 'externalCode'
            })
        ]
        
        for entity_type, filename, fields in dictionaries:
            try:
                data = self.get_all_entities(entity_type)
                self.export_to_csv(data, filename, fields)
            except Exception as e:
                logger.error(f"Ошибка экспорта справочника {entity_type}: {e}")
    
    def export_financial_reports(self):
        """Экспорт финансовых отчетов"""
        logger.info("=== ЭКСПОРТ ФИНАНСОВЫХ ОТЧЕТОВ ===")
        
        # Отчет по прибыльности
        try:
            profit_data = self.get_report_data('profit/byproduct')
            profit_fields = {
                'Товар': 'name',
                'Продажи_количество': 'sellQuantity',
                'Продажи_сумма': 'sellSum',
                'Продажи_себестоимость': 'sellCostSum',
                'Прибыль': 'profit',
                'Маржа': 'margin',
                'Рентабельность': 'returnPercent'
            }
            self.export_to_csv(profit_data, 'profit_by_product.csv', profit_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта отчета по прибыльности: {e}")
        
        # Показатели продаж
        try:
            sales_data = self.get_report_data('dashboard/sales')
            if sales_data:
                sales_fields = {
                    'Период': 'period',
                    'Продажи': 'sales',
                    'Возвраты': 'returns',
                    'Прибыль': 'profit'
                }
                self.export_to_csv(sales_data, 'sales_dashboard.csv', sales_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта показателей продаж: {e}")
    
    def export_additional_data(self):
        """Экспорт дополнительных данных"""
        logger.info("=== ЭКСПОРТ ДОПОЛНИТЕЛЬНЫХ ДАННЫХ ===")
        
        # Позиции документов
        self.export_document_positions()
        
        # Серийные номера
        self.export_serial_numbers()
        
        # Задачи
        self.export_tasks()
        
        # Файлы
        self.export_files()
        
        # Веб-хуки
        self.export_webhooks()
        
        # Дополнительные отчеты
        self.export_extended_reports()
    
    def export_document_positions(self):
        """Экспорт позиций документов"""
        logger.info("Экспортируем позиции документов...")
        
        document_types = ['demand', 'supply', 'salesreturn', 'move']
        
        for doc_type in document_types:
            try:
                # Получаем все документы этого типа
                documents = self.get_all_entities(doc_type)
                
                all_positions = []
                for doc in documents:
                    doc_id = doc['id']
                    try:
                        positions = self.make_request('GET', f'entity/{doc_type}/{doc_id}/positions')
                        for pos in positions.get('rows', []):
                            pos['document_id'] = doc_id
                            pos['document_name'] = doc.get('name', '')
                            pos['document_moment'] = doc.get('moment', '')
                            all_positions.append(pos)
                    except Exception as e:
                        logger.warning(f"Ошибка получения позиций документа {doc_id}: {e}")
                
                if all_positions:
                    position_fields = {
                        'Документ_ID': 'document_id',
                        'Документ_номер': 'document_name',
                        'Документ_дата': 'document_moment',
                        'Товар': 'assortment.name',
                        'Товар_код': 'assortment.code',
                        'Артикул': 'assortment.article',
                        'Количество': 'quantity',
                        'Цена': 'price',
                        'Сумма': 'sum',
                        'НДС': 'vat',
                        'Скидка': 'discount'
                    }
                    filename = f'{doc_type}_positions.csv'
                    self.export_to_csv(all_positions, filename, position_fields)
                    
            except Exception as e:
                logger.error(f"Ошибка экспорта позиций {doc_type}: {e}")
    
    def export_serial_numbers(self):
        """Экспорт серийных номеров"""
        try:
            serial_numbers = self.get_all_entities('consignment')
            if serial_numbers:
                serial_fields = {
                    'ID': 'id',
                    'Наименование': 'name',
                    'Серийный_номер': 'label',
                    'Товар': 'assortment.name',
                    'Код_товара': 'assortment.code'
                }
                self.export_to_csv(serial_numbers, 'serial_numbers.csv', serial_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта серийных номеров: {e}")
    
    def export_tasks(self):
        """Экспорт задач"""
        try:
            tasks = self.get_all_entities('task')
            if tasks:
                task_fields = {
                    'ID': 'id',
                    'Описание': 'description',
                    'Дата_создания': 'created',
                    'Срок_выполнения': 'deadline',
                    'Выполнена': 'done',
                    'Автор': 'author.name',
                    'Исполнитель': 'assignee.name',
                    'Тип': 'type',
                    'Приоритет': 'priority'
                }
                self.export_to_csv(tasks, 'tasks.csv', task_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта задач: {e}")
    
    def export_files(self):
        """Экспорт информации о файлах"""
        try:
            files = self.get_all_entities('files')
            if files:
                file_fields = {
                    'ID': 'id',
                    'Имя_файла': 'filename',
                    'Размер': 'size',
                    'Создан': 'created',
                    'Обновлен': 'updated',
                    'Тип': 'meta.type'
                }
                self.export_to_csv(files, 'files.csv', file_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта файлов: {e}")
    
    def export_webhooks(self):
        """Экспорт веб-хуков"""
        try:
            webhooks = self.get_all_entities('webhook')
            if webhooks:
                webhook_fields = {
                    'ID': 'id',
                    'URL': 'url',
                    'Метод': 'method',
                    'Включен': 'enabled',
                    'Действие': 'action',
                    'Тип_сущности': 'entityType'
                }
                self.export_to_csv(webhooks, 'webhooks.csv', webhook_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта веб-хуков: {e}")
    
    def export_extended_reports(self):
        """Экспорт расширенных отчетов"""
        
        # Отчет по деньгам
        try:
            money_data = self.get_report_data('money/plotseries')
            if money_data:
                money_fields = {
                    'Дата': 'date',
                    'Приход': 'credit',
                    'Расход': 'debit',
                    'Остаток': 'balance'
                }
                self.export_to_csv(money_data, 'money_flow.csv', money_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта отчета по деньгам: {e}")
        
        # Показатели заказов
        try:
            orders_data = self.get_report_data('dashboard/orders')
            if orders_data:
                orders_fields = {
                    'Период': 'period',
                    'Заказы': 'orders',
                    'Сумма_заказов': 'ordersSum'
                }
                self.export_to_csv(orders_data, 'orders_dashboard.csv', orders_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта показателей заказов: {e}")
        
        # Прибыльность по документам
        try:
            profit_docs = self.get_report_data('profit/bydocument')
            if profit_docs:
                profit_doc_fields = {
                    'Документ': 'name',
                    'Дата': 'moment',
                    'Контрагент': 'agent.name',
                    'Продажи': 'sellSum',
                    'Себестоимость': 'sellCostSum',
                    'Прибыль': 'profit',
                    'Рентабельность': 'returnPercent'
                }
                self.export_to_csv(profit_docs, 'profit_by_document.csv', profit_doc_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта прибыльности по документам: {e}")
        
        # Прибыльность по сотрудникам
        try:
            profit_employees = self.get_report_data('profit/byemployee')
            if profit_employees:
                profit_emp_fields = {
                    'Сотрудник': 'name',
                    'Продажи': 'sellSum',
                    'Себестоимость': 'sellCostSum',
                    'Прибыль': 'profit',
                    'Рентабельность': 'returnPercent'
                }
                self.export_to_csv(profit_employees, 'profit_by_employee.csv', profit_emp_fields)
        except Exception as e:
            logger.error(f"Ошибка экспорта прибыльности по сотрудникам: {e}")
    
    def export_all_data(self):
        """Полный экспорт всех доступных данных"""
        start_time = datetime.now()
        logger.info(f"Начинаем полный экспорт данных МойСклад в {start_time}")
        
        try:
            # Экспорт основных сущностей
            self.export_products()
            self.export_stock_reports()
            self.export_counterparties() 
            self.export_organizations()
            self.export_documents()
            self.export_dictionaries()
            self.export_financial_reports()
            
            # Статистика
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=== СТАТИСТИКА ЭКСПОРТА ===")
            logger.info(f"Время выполнения: {duration}")
            
            total_records = 0
            for entity_type, count in self.stats.items():
                logger.info(f"{entity_type}: {count} записей")
                total_records += count
            
            logger.info(f"ВСЕГО ЭКСПОРТИРОВАНО: {total_records} записей")
            
            # Сохраняем статистику в файл
            stats_file = os.path.join(self.output_dir, 'export_stats.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                export_info = {
                    'export_date': start_time.isoformat(),
                    'duration_seconds': duration.total_seconds(),
                    'total_records': total_records,
                    'statistics': self.stats
                }
                json.dump(export_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Экспорт завершен успешно! Файлы сохранены в папке: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка во время экспорта: {e}")
            raise


def main():
    """Главная функция"""
    
    # Ваш токен API
    TOKEN = "105d4f38eb9a02400c3a6428ea71640babe37e98"
    
    # Папка для сохранения файлов  
    OUTPUT_DIR = f"moysklad_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("🚀 Запуск полного экспорта данных МойСклад")
    print(f"📁 Файлы будут сохранены в папку: {OUTPUT_DIR}")
    print("⏱️  Процесс может занять от 5 до 30 минут в зависимости от объема данных")
    print("-" * 60)
    
    try:
        # Создаем экспортер
        exporter = MoySkladFullExporter(TOKEN, OUTPUT_DIR)
        
        # Запускаем полный экспорт
        exporter.export_all_data()
        
        print("\n" + "="*60)
        print("✅ ЭКСПОРТ ЗАВЕРШЕН УСПЕШНО!")
        print(f"📂 Проверьте папку: {OUTPUT_DIR}")
        print("📊 Файл export_stats.json содержит детальную статистику")
        print("📋 Файл moysklad_export.log содержит подробный лог выполнения")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("📋 Проверьте файл moysklad_export.log для подробной информации")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())