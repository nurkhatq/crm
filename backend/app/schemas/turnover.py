"""
Product turnover schemas
"""
from datetime import datetime
from pydantic import BaseModel


class ProductTurnoverBase(BaseModel):
    """Base product turnover schema"""
    moysklad_product_id: str
    period_start: datetime = None
    period_end: datetime = None
    stock_start: float = 0
    stock_end: float = 0
    income_quantity: float = 0
    outcome_quantity: float = 0
    income_sum: float = 0
    outcome_sum: float = 0


class ProductTurnover(ProductTurnoverBase):
    """Product turnover response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True



