"""
Product turnover model
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class ProductTurnover(Base, TimestampMixin):
    """Product turnover model"""
    __tablename__ = "product_turnovers"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    moysklad_product_id = Column(String(36), nullable=False)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    stock_start = Column(Float, default=0.0)
    stock_end = Column(Float, default=0.0)
    income_quantity = Column(Float, default=0.0)
    outcome_quantity = Column(Float, default=0.0)
    income_sum = Column(Float, default=0.0)
    outcome_sum = Column(Float, default=0.0)
    
    # Relationship
    product = relationship("Product", backref="turnovers")
    
    def __repr__(self) -> str:
        return f"<ProductTurnover(id={self.id}, product_name='{self.product_name}')>"
