"""
Product and stock models
"""
from decimal import Decimal
from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, ExternalDataMixin


class Product(Base, TimestampMixin, ExternalDataMixin):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, comment="Product name")
    code = Column(String(100), nullable=True, comment="Product code")
    article = Column(String(100), nullable=True, comment="Product article")
    description = Column(Text, nullable=True, comment="Product description")
    archived = Column(Boolean, default=False, comment="Is product archived")
    
    # Pricing
    buy_price = Column(Numeric(10, 2), nullable=True, comment="Buy price")
    sale_price = Column(Numeric(10, 2), nullable=True, comment="Sale price")
    currency = Column(String(3), default="RUB", comment="Currency code")
    
    # Product properties
    uom = Column(String(100), nullable=True, comment="Unit of measure")
    group_name = Column(String(200), nullable=True, comment="Product group name")
    supplier_name = Column(String(200), nullable=True, comment="Supplier name")
    
    # Enhanced properties
    is_service = Column(Boolean, default=False, comment="Is service")
    is_bundle = Column(Boolean, default=False, comment="Is bundle")
    country = Column(String(100), nullable=True, comment="Country")
    weight = Column(Numeric(10, 3), nullable=True, comment="Weight")
    volume = Column(Numeric(10, 3), nullable=True, comment="Volume")
    tracking_type = Column(String(50), nullable=True, comment="Tracking type")
    is_serial_trackable = Column(Boolean, default=False, comment="Is serial trackable")
    
    # Relationships
    stock = relationship("ProductStock", back_populates="product", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}')>"


class ProductStock(Base, TimestampMixin):
    """Product stock model"""
    __tablename__ = "product_stock"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    
    # Stock quantities
    stock = Column(Numeric(10, 3), default=0, comment="Current stock quantity")
    reserve = Column(Numeric(10, 3), default=0, comment="Reserved quantity")
    in_transit = Column(Numeric(10, 3), default=0, comment="In transit quantity")
    available = Column(Numeric(10, 3), default=0, comment="Available quantity")
    
    # Store information
    store_name = Column(String(200), nullable=True, comment="Store name")
    store_id = Column(String(100), nullable=True, comment="Store external ID")
    
    # Relationships
    product = relationship("Product", back_populates="stock")
    
    def __repr__(self) -> str:
        return f"<ProductStock(product_id={self.product_id}, stock={self.stock})>"
