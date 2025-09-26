import psycopg2

conn = psycopg2.connect('host=postgres port=5432 dbname=crm_dev user=postgres password=postgres')
cur = conn.cursor()

cur.execute("""
    SELECT p.name, p.buy_price, ps.stock, (ps.stock * p.buy_price) as total 
    FROM products p 
    JOIN product_stock ps ON p.id = ps.product_id 
    WHERE p.name LIKE '%Раскладушка темно-серый%'
""")

rows = cur.fetchall()
print('Расчет стоимости:')
for row in rows:
    print(f'Товар: {row[0][:50]}...')
    print(f'Цена покупки: {row[1]} ТЕН')
    print(f'Остаток: {row[2]}')
    print(f'Стоимость: {row[3]} ТЕН')
    print(f'Проверка: {row[2]} * {row[1]} = {row[2] * row[1]}')
    print('---')

conn.close()
