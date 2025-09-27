#!/usr/bin/env python3
"""
Тест API остатков МойСклад
"""
import requests
import json

# Настройки
TOKEN = "105d4f38eb9a02400c3a6428ea71640babe37e98"
BASE_URL = "https://api.moysklad.ru/api/remap/1.2"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept-Encoding": "gzip",
    "Accept": "application/json;charset=utf-8",
    "User-Agent": "MoySkladFullExporter/1.0"
}

def test_stock_endpoints():
    """Тестируем все endpoints остатков"""
    print("=== ТЕСТ API ОСТАТКОВ ===")
    
    endpoints = [
        "report/stock/all",
        "report/stock/bystore", 
        "report/stock/all/current"
    ]
    
    for endpoint in endpoints:
        print(f"\n--- Тестируем {endpoint} ---")
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params={'limit': 1})
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"Dict keys: {list(data.keys())}")
                    if 'rows' in data:
                        rows = data['rows']
                        print(f"Rows count: {len(rows)}")
                        if rows:
                            print(f"First row keys: {list(rows[0].keys())}")
                            print(f"Sample data: {json.dumps(rows[0], ensure_ascii=False, indent=2)[:500]}...")
                    elif 'meta' in data:
                        meta = data['meta']
                        print(f"Meta keys: {list(meta.keys())}")
                        print(f"Total size: {meta.get('size', 'unknown')}")
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
                    if data:
                        print(f"First item keys: {list(data[0].keys())}")
                        print(f"Sample data: {json.dumps(data[0], ensure_ascii=False, indent=2)[:500]}...")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

def test_stock_data_structure():
    """Тестируем структуру данных остатков"""
    print("\n=== АНАЛИЗ СТРУКТУРЫ ДАННЫХ ОСТАТКОВ ===")
    
    try:
        # Получаем несколько записей для анализа
        response = requests.get(f"{BASE_URL}/report/stock/all", headers=headers, params={'limit': 3})
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get('rows', [])
            
            print(f"Получено {len(rows)} записей остатков")
            
            for i, row in enumerate(rows):
                print(f"\n--- Запись {i+1} ---")
                print(f"Основные поля:")
                print(f"  name: {row.get('name', 'N/A')}")
                print(f"  code: {row.get('code', 'N/A')}")
                print(f"  article: {row.get('article', 'N/A')}")
                print(f"  stock: {row.get('stock', 'N/A')}")
                print(f"  reserve: {row.get('reserve', 'N/A')}")
                print(f"  inTransit: {row.get('inTransit', 'N/A')}")
                print(f"  quantity: {row.get('quantity', 'N/A')}")
                
                # Проверяем meta.href
                meta = row.get('meta', {})
                href = meta.get('href', '')
                print(f"  meta.href: {href}")
                
                # Проверяем stockByStore
                stock_by_store = row.get('stockByStore', [])
                print(f"  stockByStore: {len(stock_by_store)} записей")
                
                if stock_by_store:
                    print(f"    Первая запись stockByStore:")
                    first_store = stock_by_store[0]
                    print(f"      store name: {first_store.get('name', 'N/A')}")
                    print(f"      stock: {first_store.get('stock', 'N/A')}")
                    print(f"      reserve: {first_store.get('reserve', 'N/A')}")
                
                # Проверяем другие поля
                print(f"  Другие поля: {list(row.keys())}")
                
        else:
            print(f"Ошибка получения данных: {response.text}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_stock_endpoints()
    test_stock_data_structure()



