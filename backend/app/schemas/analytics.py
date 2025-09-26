"""
Analytics schemas
"""
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class KPIMetrics(BaseModel):
    """KPI metrics schema"""
    total_products: int = Field(..., description="Total number of products")
    total_customers: int = Field(..., description="Total number of customers")
    total_documents: int = Field(..., description="Total number of documents")
    total_revenue: Decimal = Field(..., description="Total revenue")
    total_stock_value: Decimal = Field(..., description="Total stock value")
    low_stock_products: int = Field(..., description="Number of low stock products")
    last_sync: Optional[datetime] = Field(None, description="Last sync time")
    currency: Optional[str] = Field("₽", description="Main currency")


class TopProduct(BaseModel):
    """Top product schema"""
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    sales_count: int = Field(..., description="Number of sales")
    revenue: Decimal = Field(..., description="Total revenue")
    stock: Decimal = Field(..., description="Current stock")


class TopProducts(BaseModel):
    """Top products response schema"""
    products: List[TopProduct] = Field(..., description="List of top products")
    period: str = Field(..., description="Analysis period")


class ForecastPoint(BaseModel):
    """Forecast point schema"""
    date: datetime = Field(..., description="Forecast date")
    predicted_sales: Decimal = Field(..., description="Predicted sales quantity")
    confidence_lower: Decimal = Field(..., description="Lower confidence bound")
    confidence_upper: Decimal = Field(..., description="Upper confidence bound")


class ProductForecast(BaseModel):
    """Product forecast schema"""
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    forecast_points: List[ForecastPoint] = Field(..., description="Forecast data points")
    method: str = Field(..., description="Forecast method used")
    accuracy: Optional[Decimal] = Field(None, description="Forecast accuracy")
