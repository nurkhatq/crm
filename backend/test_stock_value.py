import asyncio
import sys
sys.path.append('/app')

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test_stock_value():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT COALESCE(SUM(ps.stock * CASE 
                WHEN p.sale_price > 0 THEN p.sale_price 
                WHEN p.buy_price > 0 THEN p.buy_price 
                ELSE 0 
            END), 0) as total_stock_value 
            FROM product_stock ps 
            JOIN products p ON ps.product_id = p.id
        """))
        value = result.scalar()
        print(f"Stock value from FastAPI: {value}")
        print(f"Type: {type(value)}")

if __name__ == "__main__":
    asyncio.run(test_stock_value())
