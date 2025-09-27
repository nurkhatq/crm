"""
Store model
"""
from sqlalchemy import Column, String, Integer, Boolean, Text
from app.models.base import Base, TimestampMixin


class Store(Base, TimestampMixin):
    """Store model"""
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    archived = Column(Boolean, default=False)
    
    def __repr__(self) -> str:
        return f"<Store(id={self.id}, name='{self.name}')>"
