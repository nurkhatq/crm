"""
Document schemas
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema"""
    name: str = Field(..., description="Document number")
    document_type: str = Field(..., description="Document type")
    moment: Optional[datetime] = Field(None, description="Document date")
    sum: Optional[Decimal] = Field(None, description="Document sum")
    currency: str = Field("RUB", description="Currency code")
    applicable: bool = Field(False, description="Is document applied")
    state_name: Optional[str] = Field(None, description="State name")
    organization_name: Optional[str] = Field(None, description="Organization name")
    store_name: Optional[str] = Field(None, description="Store name")


class DocumentCreate(DocumentBase):
    """Document creation schema"""
    external_id: str = Field(..., description="External system ID")
    external_raw: Optional[str] = Field(None, description="Raw JSON data")
    customer_id: Optional[int] = Field(None, description="Customer ID")


class DocumentUpdate(BaseModel):
    """Document update schema"""
    name: Optional[str] = None
    document_type: Optional[str] = None
    moment: Optional[datetime] = None
    sum: Optional[Decimal] = None
    currency: Optional[str] = None
    applicable: Optional[bool] = None
    state_name: Optional[str] = None
    organization_name: Optional[str] = None
    store_name: Optional[str] = None
    customer_id: Optional[int] = None


class Document(DocumentBase):
    """Document response schema"""
    id: int
    external_id: str
    external_updated: Optional[datetime] = None
    customer_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
