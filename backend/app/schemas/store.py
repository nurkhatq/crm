"""
Store schemas
"""
from datetime import datetime
from pydantic import BaseModel


class StoreBase(BaseModel):
    """Base store schema"""
    external_id: str
    name: str
    code: str = None
    address: str = None
    archived: bool = False


class Store(StoreBase):
    """Store response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True



