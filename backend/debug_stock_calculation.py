import psycopg2

conn = psycopg2.connect('host=postgres port=5432 dbname=crm_dev user=postgres password=postgres')
cur = conn.cursor()

print("=== АНАЛИЗ РАСЧЕТА СТОИМОСТИ ОСТАТКОВ ===\n")

# Проверим SQL запрос, который используется в API
cur.execute("""
    SELECT 
        COUNT(*) as total_products,
        SUM(ps.stock) as total_stock_quantity,
        AVG(ps.stock) as avg_stock_per_product,
        MAX(ps.stock) as max_stock,
        MIN(ps.stock) as min_stock
    FROM product_stock ps 
    JOIN products p ON ps.product_id = p.id
    WHERE ps.stock > 0
""")

stats = cur.fetchone()
print(f"Общая статистика:")
print(f"  Товаров с остатками: {stats[0]}")
print(f"  Общее количество на складе: {stats[1]:,.0f} шт")
print(f"  Средний остаток на товар: {stats[2]:,.1f} шт")
print(f"  Максимальный остаток: {stats[3]:,.0f} шт")
print(f"  Минимальный остаток: {stats[4]:,.0f} шт")

# Проверим расчет стоимости по текущей логике API
cur.execute("""
    SELECT 
        COALESCE(SUM(ps.stock * CASE 
            WHEN p.sale_price > 0 THEN p.sale_price 
            WHEN p.buy_price > 0 THEN p.buy_price 
            ELSE 0 
        END), 0) as total_stock_value
    FROM product_stock ps 
    JOIN products p ON ps.product_id = p.id
    WHERE ps.stock > 0
""")

total_value = cur.fetchone()[0]
print(f"\nОбщая стоимость остатков (текущая логика): {total_value:,.0f}")

# Детальный анализ по товарам с наибольшей стоимостью
cur.execute("""
    SELECT 
        p.name,
        p.sale_price,
        p.buy_price,
        ps.stock,
        CASE 
            WHEN p.sale_price > 0 THEN p.sale_price 
            WHEN p.buy_price > 0 THEN p.buy_price 
            ELSE 0 
        END as used_price,
        ps.stock * CASE 
            WHEN p.sale_price > 0 THEN p.sale_price 
            WHEN p.buy_price > 0 THEN p.buy_price 
            ELSE 0 
        END as item_value
    FROM product_stock ps 
    JOIN products p ON ps.product_id = p.id
    WHERE ps.stock > 0
    ORDER BY ps.stock * CASE 
        WHEN p.sale_price > 0 THEN p.sale_price 
        WHEN p.buy_price > 0 THEN p.buy_price 
        ELSE 0 
    END DESC
    LIMIT 10
""")

print(f"\nТОП-10 товаров по стоимости остатков:")
print("=" * 100)
for row in cur.fetchall():
    name, sale_price, buy_price, stock, used_price, item_value = row
    print(f"Товар: {name[:40]}...")
    print(f"  Цена продажи: {sale_price:,.0f} ТЕН" if sale_price > 0 else "  Цена продажи: не указана")
    print(f"  Цена покупки: {buy_price:,.0f} ТЕН" if buy_price > 0 else "  Цена покупки: не указана")
    print(f"  Используемая цена: {used_price:,.0f} ТЕН")
    print(f"  Остаток: {stock} шт")
    print(f"  Стоимость остатка: {item_value:,.0f} ТЕН")
    print("-" * 50)

# Проверим товары без цен
cur.execute("""
    SELECT COUNT(*) 
    FROM product_stock ps 
    JOIN products p ON ps.product_id = p.id
    WHERE ps.stock > 0 
    AND p.sale_price <= 0 
    AND p.buy_price <= 0
""")

no_price_count = cur.fetchone()[0]
print(f"\nТоваров без цен (sale_price <= 0 AND buy_price <= 0): {no_price_count}")

# Проверим товары только с ценой покупки
cur.execute("""
    SELECT COUNT(*), SUM(ps.stock * p.buy_price)
    FROM product_stock ps 
    JOIN products p ON ps.product_id = p.id
    WHERE ps.stock > 0 
    AND p.sale_price <= 0 
    AND p.buy_price > 0
""")

buy_only = cur.fetchone()
print(f"Товаров только с ценой покупки: {buy_only[0]}")
print(f"Их стоимость: {buy_only[1]:,.0f} ТЕН")

# Проверим товары только с ценой продажи
cur.execute("""
    SELECT COUNT(*), SUM(ps.stock * p.sale_price)
    FROM product_stock ps 
    JOIN products p ON ps.product_id = p.id
    WHERE ps.stock > 0 
    AND p.sale_price > 0
""")

sale_only = cur.fetchone()
print(f"Товаров с ценой продажи: {sale_only[0]}")
print(f"Их стоимость: {sale_only[1]:,.0f} ТЕН")

conn.close()
