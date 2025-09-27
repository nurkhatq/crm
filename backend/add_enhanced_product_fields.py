#!/usr/bin/env python3
"""
Добавление новых полей в таблицу products для улучшенной синхронизации
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_enhanced_fields():
    """Добавляем новые поля в таблицу products"""
    
    # Создаем синхронный движок
    engine = create_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
        echo=True
    )
    
    with engine.connect() as conn:
        # Начинаем транзакцию
        trans = conn.begin()
        
        try:
            # Добавляем новые поля
            print("Добавляем новые поля в таблицу products...")
            
            # is_service
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS is_service BOOLEAN DEFAULT FALSE
            """))
            print("✓ Добавлено поле is_service")
            
            # is_bundle
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS is_bundle BOOLEAN DEFAULT FALSE
            """))
            print("✓ Добавлено поле is_bundle")
            
            # country
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS country VARCHAR(100)
            """))
            print("✓ Добавлено поле country")
            
            # weight
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS weight DECIMAL(10,3)
            """))
            print("✓ Добавлено поле weight")
            
            # volume
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS volume DECIMAL(10,3)
            """))
            print("✓ Добавлено поле volume")
            
            # tracking_type
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS tracking_type VARCHAR(50)
            """))
            print("✓ Добавлено поле tracking_type")
            
            # is_serial_trackable
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS is_serial_trackable BOOLEAN DEFAULT FALSE
            """))
            print("✓ Добавлено поле is_serial_trackable")
            
            # Добавляем комментарии
            conn.execute(text("""
                COMMENT ON COLUMN products.is_service IS 'Is service';
                COMMENT ON COLUMN products.is_bundle IS 'Is bundle';
                COMMENT ON COLUMN products.country IS 'Country';
                COMMENT ON COLUMN products.weight IS 'Weight';
                COMMENT ON COLUMN products.volume IS 'Volume';
                COMMENT ON COLUMN products.tracking_type IS 'Tracking type';
                COMMENT ON COLUMN products.is_serial_trackable IS 'Is serial trackable';
            """))
            print("✓ Добавлены комментарии к полям")
            
            # Подтверждаем транзакцию
            trans.commit()
            print("\n🎉 Все поля успешно добавлены в таблицу products!")
            
        except Exception as e:
            # Откатываем транзакцию в случае ошибки
            trans.rollback()
            print(f"\n❌ Ошибка при добавлении полей: {e}")
            raise

if __name__ == "__main__":
    add_enhanced_fields()



