"""
Document models
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, ExternalDataMixin


class Document(Base, TimestampMixin, ExternalDataMixin):
    """Document model (orders, sales, purchases, etc.)"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="Document number")
    document_type = Column(String(50), nullable=False, comment="Document type")
    
    # Document details
    moment = Column(DateTime(timezone=True), nullable=True, comment="Document date")
    sum = Column(Numeric(12, 2), nullable=True, comment="Document sum")
    currency = Column(String(3), default="RUB", comment="Currency code")
    
    # Status
    applicable = Column(Boolean, default=False, comment="Is document applied")
    state_name = Column(String(100), nullable=True, comment="State name")
    
    # Related entities
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    organization_name = Column(String(200), nullable=True, comment="Organization name")
    store_name = Column(String(200), nullable=True, comment="Store name")
    
    # Relationships
    customer = relationship("Customer", back_populates="documents")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, type='{self.document_type}', name='{self.name}')>"
