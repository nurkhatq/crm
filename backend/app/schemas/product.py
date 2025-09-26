"""
Product schemas
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., description="Product name")
    code: Optional[str] = Field(None, description="Product code")
    article: Optional[str] = Field(None, description="Product article")
    description: Optional[str] = Field(None, description="Product description")
    archived: bool = Field(False, description="Is product archived")
    buy_price: Optional[Decimal] = Field(None, description="Buy price")
    sale_price: Optional[Decimal] = Field(None, description="Sale price")
    currency: Optional[str] = Field("RUB", description="Currency code")
    uom: Optional[str] = Field(None, description="Unit of measure")
    group_name: Optional[str] = Field(None, description="Product group name")
    supplier_name: Optional[str] = Field(None, description="Supplier name")


class ProductCreate(ProductBase):
    """Product creation schema"""
    external_id: str = Field(..., description="External system ID")
    external_raw: Optional[str] = Field(None, description="Raw JSON data")


class ProductUpdate(BaseModel):
    """Product update schema"""
    name: Optional[str] = None
    code: Optional[str] = None
    article: Optional[str] = None
    description: Optional[str] = None
    archived: Optional[bool] = None
    buy_price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    currency: Optional[str] = None
    uom: Optional[str] = None
    group_name: Optional[str] = None
    supplier_name: Optional[str] = None


class Product(ProductBase):
    """Product response schema"""
    id: int
    external_id: str
    external_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductStockBase(BaseModel):
    """Base product stock schema"""
    stock: Optional[Decimal] = Field(0, description="Current stock quantity")
    reserve: Optional[Decimal] = Field(0, description="Reserved quantity")
    in_transit: Optional[Decimal] = Field(0, description="In transit quantity")
    available: Optional[Decimal] = Field(0, description="Available quantity")
    store_name: Optional[str] = Field(None, description="Store name")
    store_id: Optional[str] = Field(None, description="Store external ID")


class ProductStock(ProductStockBase):
    """Product stock response schema"""
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductWithStock(Product):
    """Product with stock information"""
    stock: Optional[ProductStock] = None


class ProductStockWithProduct(ProductStock):
    """Product stock with product information"""
    product: Optional[Product] = None
