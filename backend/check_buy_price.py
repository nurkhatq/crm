import psycopg2

conn = psycopg2.connect('host=postgres port=5432 dbname=crm_dev user=postgres password=postgres')
cur = conn.cursor()

# Проверим несколько товаров с разными ценами покупки
cur.execute("""
    SELECT p.name, p.buy_price, p.sale_price, ps.stock, 
           (ps.stock * p.buy_price) as total_buy_value,
           (ps.stock * p.sale_price) as total_sale_value
    FROM products p 
    JOIN product_stock ps ON p.id = ps.product_id 
    WHERE p.buy_price > 0 
    ORDER BY p.buy_price DESC 
    LIMIT 10
""")

rows = cur.fetchall()
print('Анализ цен покупки:')
print('=' * 80)
for row in rows:
    print(f'Товар: {row[0][:40]}...')
    print(f'  Цена покупки: {row[1]:,.0f} ТЕН')
    print(f'  Цена продажи: {row[2]:,.0f} ТЕН' if row[2] > 0 else '  Цена продажи: Не указана')
    print(f'  Остаток: {row[3]} шт')
    print(f'  Стоимость по цене покупки: {row[4]:,.0f} ТЕН')
    if row[2] > 0:
        print(f'  Стоимость по цене продажи: {row[5]:,.0f} ТЕН')
    print()

# Проверим соотношение цен
cur.execute("""
    SELECT 
        COUNT(*) as total_products,
        AVG(buy_price) as avg_buy_price,
        AVG(sale_price) as avg_sale_price,
        MIN(buy_price) as min_buy_price,
        MAX(buy_price) as max_buy_price
    FROM products 
    WHERE buy_price > 0
""")

stats = cur.fetchone()
print('Статистика цен:')
print(f'Всего товаров с ценой покупки: {stats[0]}')
print(f'Средняя цена покупки: {stats[1]:,.0f} ТЕН')
print(f'Средняя цена продажи: {stats[2]:,.0f} ТЕН')
print(f'Минимальная цена покупки: {stats[3]:,.0f} ТЕН')
print(f'Максимальная цена покупки: {stats[4]:,.0f} ТЕН')

conn.close()
