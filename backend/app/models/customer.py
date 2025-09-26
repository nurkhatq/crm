"""
Customer model
"""
from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, ExternalDataMixin


class Customer(Base, TimestampMixin, ExternalDataMixin):
    """Customer/Counterparty model"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, comment="Customer name")
    code = Column(String(100), nullable=True, comment="Customer code")
    legal_title = Column(String(500), nullable=True, comment="Legal title")
    
    # Contact information
    email = Column(String(255), nullable=True, comment="Email address")
    phone = Column(String(50), nullable=True, comment="Phone number")
    
    # Legal information
    inn = Column(String(12), nullable=True, comment="INN")
    kpp = Column(String(9), nullable=True, comment="KPP")
    
    # Address
    address = Column(Text, nullable=True, comment="Full address")
    postal_address = Column(Text, nullable=True, comment="Postal address")
    
    # Status
    archived = Column(Boolean, default=False, comment="Is customer archived")
    
    # Relationships
    documents = relationship("Document", back_populates="customer")
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}')>"
