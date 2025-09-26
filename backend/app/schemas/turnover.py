"""
Product turnover schemas
"""
from datetime import datetime
from pydantic import BaseModel


class ProductTurnoverBase(BaseModel):
    """Base product turnover schema"""
    product_external_id: str
    product_name: str
    product_code: str = None
    stock_at_period_start: float = 0
    income: float = 0
    outcome: float = 0
    stock_at_period_end: float = 0


class ProductTurnover(ProductTurnoverBase):
    """Product turnover response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
