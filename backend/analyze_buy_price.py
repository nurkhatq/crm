import psycopg2

conn = psycopg2.connect('host=postgres port=5432 dbname=crm_dev user=postgres password=postgres')
cur = conn.cursor()

print("=== АНАЛИЗ ЦЕНЫ ПОКУПКИ В МОЙСКЛАД ===\n")

# Проверим несколько товаров с разными ценами и остатками
cur.execute("""
    SELECT 
        p.name,
        p.buy_price,
        ps.stock,
        p.article,
        p.code,
        p.description
    FROM products p 
    JOIN product_stock ps ON p.id = ps.product_id 
    WHERE p.buy_price > 0 
    AND ps.stock > 0
    ORDER BY p.buy_price DESC 
    LIMIT 15
""")

rows = cur.fetchall()
print("ТОП-15 товаров по цене покупки:")
print("=" * 100)
for row in rows:
    name, buy_price, stock, article, code, description = row
    print(f"Товар: {name[:50]}...")
    print(f"  Код: {code}")
    print(f"  Артикул: {article}")
    print(f"  Цена покупки: {buy_price:,.0f} ТЕН")
    print(f"  Остаток: {stock} шт")
    print(f"  Описание: {description[:100] if description else 'Нет'}...")
    
    # Проверим логику: если это цена за штуку, то при большом остатке будет огромная стоимость
    if stock > 1:
        total_cost = buy_price * stock
        print(f"  Стоимость остатка: {total_cost:,.0f} ТЕН ({stock} × {buy_price:,.0f})")
    
    print("-" * 80)

# Проверим товары с маленькими остатками
print("\n\nТовары с маленькими остатками (1-5 шт):")
print("=" * 100)
cur.execute("""
    SELECT 
        p.name,
        p.buy_price,
        ps.stock,
        p.code
    FROM products p 
    JOIN product_stock ps ON p.id = ps.product_id 
    WHERE p.buy_price > 0 
    AND ps.stock BETWEEN 1 AND 5
    ORDER BY p.buy_price DESC 
    LIMIT 10
""")

rows = cur.fetchall()
for row in rows:
    name, buy_price, stock, code = row
    print(f"Товар: {name[:40]}...")
    print(f"  Код: {code}")
    print(f"  Цена покупки: {buy_price:,.0f} ТЕН")
    print(f"  Остаток: {stock} шт")
    print(f"  Стоимость остатка: {buy_price * stock:,.0f} ТЕН")
    print("-" * 50)

# Проверим товары с большими остатками
print("\n\nТовары с большими остатками (>50 шт):")
print("=" * 100)
cur.execute("""
    SELECT 
        p.name,
        p.buy_price,
        ps.stock,
        p.code
    FROM products p 
    JOIN product_stock ps ON p.id = ps.product_id 
    WHERE p.buy_price > 0 
    AND ps.stock > 50
    ORDER BY ps.stock DESC 
    LIMIT 10
""")

rows = cur.fetchall()
for row in rows:
    name, buy_price, stock, code = row
    total_cost = buy_price * stock
    print(f"Товар: {name[:40]}...")
    print(f"  Код: {code}")
    print(f"  Цена покупки: {buy_price:,.0f} ТЕН")
    print(f"  Остаток: {stock} шт")
    print(f"  Стоимость остатка: {total_cost:,.0f} ТЕН")
    print("-" * 50)

conn.close()
