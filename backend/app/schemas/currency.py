"""
Currency schemas
"""
from datetime import datetime
from pydantic import BaseModel


class CurrencyBase(BaseModel):
    """Base currency schema"""
    external_id: str
    name: str
    code: str
    full_name: str = None
    rate: float = 1.0
    indirect: bool = False
    archived: bool = False


class Currency(CurrencyBase):
    """Currency response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
