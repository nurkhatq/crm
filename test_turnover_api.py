#!/usr/bin/env python3
"""
Тест API оборотов МойСклад
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

def test_turnover_api():
    """Тестируем API оборотов"""
    print("=== ТЕСТ API ОБОРОТОВ ===")
    
    # Тест 1: Без параметров
    print("\n1. Тест без параметров:")
    try:
        response = requests.get(f"{BASE_URL}/report/turnover/all", headers=headers, params={'limit': 1})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data type: {type(data)}")
            if isinstance(data, list):
                print(f"List length: {len(data)}")
                if data:
                    print(f"First item keys: {list(data[0].keys())}")
            elif isinstance(data, dict):
                print(f"Dict keys: {list(data.keys())}")
                if 'rows' in data:
                    print(f"Rows count: {len(data.get('rows', []))}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Тест 2: С параметрами даты
    print("\n2. Тест с параметрами даты:")
    try:
        params = {
            'limit': 1,
            'momentFrom': '2024-01-01 00:00:00',
            'momentTo': '2024-12-31 23:59:59'
        }
        response = requests.get(f"{BASE_URL}/report/turnover/all", headers=headers, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data type: {type(data)}")
            if isinstance(data, list):
                print(f"List length: {len(data)}")
                if data:
                    print(f"First item keys: {list(data[0].keys())}")
            elif isinstance(data, dict):
                print(f"Dict keys: {list(data.keys())}")
                if 'rows' in data:
                    print(f"Rows count: {len(data.get('rows', []))}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_turnover_api()
