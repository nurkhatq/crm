"""
Main API router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import products, customers, documents, analytics, sync, auth, employees, turnover, stores, currencies

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(sync.router, prefix="/connectors/moysklad", tags=["sync"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(turnover.router, prefix="/product-turnover", tags=["turnover"])
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])
api_router.include_router(currencies.router, prefix="/currencies", tags=["currencies"])
