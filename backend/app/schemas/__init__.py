"""
Pydantic schemas for API serialization
"""
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductStock
from app.schemas.customer import Customer, CustomerCreate, CustomerUpdate
from app.schemas.document import Document, DocumentCreate, DocumentUpdate
from app.schemas.user import User, UserCreate, UserUpdate, UserLogin
from app.schemas.auth import Token, TokenData
from app.schemas.sync import SyncLog, SyncRequest, SyncResponse
from app.schemas.analytics import KPIMetrics, TopProducts, ProductForecast

__all__ = [
    "Product", "ProductCreate", "ProductUpdate", "ProductStock",
    "Customer", "CustomerCreate", "CustomerUpdate", 
    "Document", "DocumentCreate", "DocumentUpdate",
    "User", "UserCreate", "UserUpdate", "UserLogin",
    "Token", "TokenData",
    "SyncLog", "SyncRequest", "SyncResponse",
    "KPIMetrics", "TopProducts", "ProductForecast"
]
