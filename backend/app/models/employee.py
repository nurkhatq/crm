"""
Employee model
"""
from sqlalchemy import Column, String, Integer
from app.models.base import Base, TimestampMixin


class Employee(Base, TimestampMixin):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name='{self.name}')>"
