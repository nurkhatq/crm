"""
Customer schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class CustomerBase(BaseModel):
    """Base customer schema"""
    name: str = Field(..., description="Customer name")
    code: Optional[str] = Field(None, description="Customer code")
    legal_title: Optional[str] = Field(None, description="Legal title")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    inn: Optional[str] = Field(None, description="INN")
    kpp: Optional[str] = Field(None, description="KPP")
    address: Optional[str] = Field(None, description="Full address")
    postal_address: Optional[str] = Field(None, description="Postal address")
    archived: bool = Field(False, description="Is customer archived")


class CustomerCreate(CustomerBase):
    """Customer creation schema"""
    external_id: str = Field(..., description="External system ID")
    external_raw: Optional[str] = Field(None, description="Raw JSON data")


class CustomerUpdate(BaseModel):
    """Customer update schema"""
    name: Optional[str] = None
    code: Optional[str] = None
    legal_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    address: Optional[str] = None
    postal_address: Optional[str] = None
    archived: Optional[bool] = None


class Customer(CustomerBase):
    """Customer response schema"""
    id: int
    external_id: Optional[str] = None
    external_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
