import psycopg2

conn = psycopg2.connect('host=postgres port=5432 dbname=crm_dev user=postgres password=postgres')
cur = conn.cursor()

cur.execute("SELECT currency FROM products WHERE currency IS NOT NULL AND currency != '' LIMIT 1")
result = cur.fetchone()
print('Основная валюта в базе:', result[0] if result else 'Не найдена')

# Проверим все валюты
cur.execute("SELECT DISTINCT currency, COUNT(*) FROM products WHERE currency IS NOT NULL AND currency != '' GROUP BY currency")
currencies = cur.fetchall()
print('\nВсе валюты в базе:')
for curr, count in currencies:
    print(f'  {curr}: {count} товаров')

conn.close()
