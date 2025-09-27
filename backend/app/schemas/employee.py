"""
Employee schemas
"""
from datetime import datetime
from pydantic import BaseModel


class EmployeeBase(BaseModel):
    """Base employee schema"""
    external_id: str
    name: str
    email: str = None
    position: str = None


class Employee(EmployeeBase):
    """Employee response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True



