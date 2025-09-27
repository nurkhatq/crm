#!/usr/bin/env python3
"""
Тестовый скрипт для анализа API МойСклад
"""
import requests
import json
import time
from typing import Dict, Any, List

# Настройки из .env
MOYSKLAD_TOKEN = "105d4f38eb9a02400c3a6428ea71640babe37e98"
BASE_URL = "https://api.moysklad.ru/api/remap/1.2"

headers = {
    'Authorization': f'Bearer {MOYSKLAD_TOKEN}',
    'Accept-Encoding': 'gzip',
    'Accept': 'application/json;charset=utf-8',
    'User-Agent': 'MoySkladFullExporter/1.0'
}

def test_api_endpoint(endpoint: str, params: Dict = None, description: str = ""):
    """Тестирует API endpoint"""
    print(f"\n=== {description or endpoint} ===")
    
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, headers=headers, params=params or {})
        
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get('rows', [])
            meta = data.get('meta', {})
            
            print(f"Total rows: {meta.get('size', len(rows))}")
            print(f"Current page rows: {len(rows)}")
            print(f"Has next: {'nextHref' in meta}")
            
            if rows:
                first_item = rows[0]
                print(f"Fields in first item: {list(first_item.keys())}")
                
                # Показываем пример данных (первые 3 поля)
                for i, (key, value) in enumerate(list(first_item.items())[:3]):
                    print(f"  {key}: {value}")
                
                return data
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def analyze_expand_options():
    """Анализирует возможности expand для товаров"""
    print("\n" + "="*60)
    print("АНАЛИЗ EXPAND ОПЦИЙ ДЛЯ ТОВАРОВ")
    print("="*60)
    
    # Тест без expand
    print("\n1. Товары БЕЗ expand:")
    test_api_endpoint("entity/product", {"limit": 1}, "Товары без expand")
    
    # Тест с базовым expand
    print("\n2. Товары с базовым expand:")
    test_api_endpoint("entity/product", {
        "limit": 1,
        "expand": "owner,group,uom"
    }, "Товары с базовым expand")
    
    # Тест с расширенным expand
    print("\n3. Товары с расширенным expand:")
    test_api_endpoint("entity/product", {
        "limit": 1,
        "expand": "owner,group,uom,supplier,buyPrice.currency,salePrices.currency,images,attributes"
    }, "Товары с расширенным expand")
    
    # Тест с максимальным expand
    print("\n4. Товары с максимальным expand:")
    test_api_endpoint("entity/product", {
        "limit": 1,
        "expand": "owner,group,uom,supplier,buyPrice.currency,salePrices.currency,images,attributes,productFolder,country"
    }, "Товары с максимальным expand")

def test_all_available_endpoints():
    """Тестирует все доступные endpoints"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ВСЕХ ДОСТУПНЫХ ENDPOINTS")
    print("="*60)
    
    endpoints = [
        # Товары и ассортимент
        ("entity/product", "Товары"),
        ("entity/assortment", "Ассортимент (все товары)"),
        ("entity/service", "Услуги"),
        ("entity/bundle", "Комплекты"),
        ("entity/variant", "Модификации товаров"),
        
        # Остатки
        ("report/stock/all", "Остатки всех товаров"),
        ("report/stock/bystore", "Остатки по складам"),
        ("report/stock/all/current", "Текущие остатки"),
        
        # Контрагенты
        ("entity/counterparty", "Контрагенты"),
        ("entity/organization", "Организации"),
        
        # Документы продаж
        ("entity/customerorder", "Заказы покупателей"),
        ("entity/demand", "Отгрузки"),
        ("entity/invoiceout", "Счета покупателям"),
        ("entity/salesreturn", "Возвраты покупателей"),
        ("entity/retailsale", "Розничные продажи"),
        
        # Документы закупок
        ("entity/purchaseorder", "Заказы поставщикам"),
        ("entity/supply", "Приемки"),
        ("entity/invoicein", "Счета поставщиков"),
        ("entity/purchasereturn", "Возвраты поставщикам"),
        
        # Складские документы
        ("entity/store", "Склады"),
        ("entity/enter", "Оприходования"),
        ("entity/loss", "Списания"),
        ("entity/move", "Перемещения"),
        ("entity/inventory", "Инвентаризации"),
        
        # Справочники
        ("entity/currency", "Валюты"),
        ("entity/uom", "Единицы измерения"),
        ("entity/productfolder", "Группы товаров"),
        ("entity/project", "Проекты"),
        ("entity/contract", "Договоры"),
        ("entity/pricetype", "Типы цен"),
        ("entity/country", "Страны"),
        
        # Финансовые отчеты
        ("report/money/plotseries", "Движение денежных средств"),
        ("report/money/cash", "Остатки в кассах"),
        ("report/profit/byproduct", "Прибыльность по товарам"),
        ("report/dashboard/sales", "Показатели продаж"),
        ("report/dashboard/orders", "Показатели заказов"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        data = test_api_endpoint(endpoint, {"limit": 1}, description)
        results[endpoint] = {
            'description': description,
            'has_data': data is not None,
            'row_count': data.get('meta', {}).get('size', 0) if data else 0
        }
        time.sleep(0.1)  # Rate limiting
    
    return results

def analyze_current_sync_data():
    """Анализирует текущие данные в базе"""
    print("\n" + "="*60)
    print("АНАЛИЗ ТЕКУЩИХ ДАННЫХ В БАЗЕ")
    print("="*60)
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Товары
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            product_count = result.scalar()
            print(f"Товаров в базе: {product_count}")
            
            # Клиенты
            result = conn.execute(text("SELECT COUNT(*) FROM customers"))
            customer_count = result.scalar()
            print(f"Клиентов в базе: {customer_count}")
            
            # Документы
            result = conn.execute(text("SELECT COUNT(*) FROM documents"))
            document_count = result.scalar()
            print(f"Документов в базе: {document_count}")
            
            # Остатки
            result = conn.execute(text("SELECT COUNT(*) FROM product_stock"))
            stock_count = result.scalar()
            print(f"Записей остатков: {stock_count}")
            
            # Пример товара с данными
            result = conn.execute(text("""
                SELECT name, code, article, buy_price, sale_price, currency, 
                       uom, group_name, supplier_name, external_raw IS NOT NULL as has_raw_data
                FROM products 
                LIMIT 3
            """))
            products = result.fetchall()
            print(f"\nПримеры товаров:")
            for product in products:
                print(f"  {product[0]} | {product[1]} | {product[2]} | {product[3]} | {product[4]} | {product[5]} | {product[6]} | {product[7]} | {product[8]} | Raw: {product[9]}")
                
    except Exception as e:
        print(f"Ошибка подключения к базе: {e}")

if __name__ == "__main__":
    print("НАЧИНАЕМ АНАЛИЗ API МОЙСКЛАД")
    print("="*60)
    
    # 1. Анализ expand опций
    analyze_expand_options()
    
    # 2. Тестирование всех endpoints
    results = test_all_available_endpoints()
    
    # 3. Анализ текущих данных
    analyze_current_sync_data()
    
    # 4. Сводка результатов
    print("\n" + "="*60)
    print("СВОДКА РЕЗУЛЬТАТОВ")
    print("="*60)
    
    available_endpoints = [k for k, v in results.items() if v['has_data'] and v['row_count'] > 0]
    unavailable_endpoints = [k for k, v in results.items() if not v['has_data'] or v['row_count'] == 0]
    
    print(f"Доступных endpoints с данными: {len(available_endpoints)}")
    print(f"Недоступных/пустых endpoints: {len(unavailable_endpoints)}")
    
    print(f"\nДоступные endpoints:")
    for endpoint in available_endpoints:
        info = results[endpoint]
        print(f"  {endpoint} - {info['description']} ({info['row_count']} записей)")
    
    print(f"\nНедоступные endpoints:")
    for endpoint in unavailable_endpoints:
        info = results[endpoint]
        print(f"  {endpoint} - {info['description']}")



