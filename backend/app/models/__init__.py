# backend/app/models/__init__.py - Импорт всех моделей

from app.models.base import Base
from app.models.product import Product, ProductStock
from app.models.customer import Customer
from app.models.document import Document
from app.models.employee import Employee
from app.models.user import User
from app.models.sync_log import SyncLog
from app.models.turnover import ProductTurnover
from app.models.store import Store

# Создаем алиас для StockReport (это ProductStock)
StockReport = ProductStock

# Экспорт всех моделей
__all__ = [
    'Base',
    'Product', 
    'ProductStock',
    'StockReport',  # Алиас для обратной совместимости
    'Customer', 
    'Document', 
    'Employee',
    'User',
    'SyncLog',
    'ProductTurnover',
    'Store'
]